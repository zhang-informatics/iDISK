import warnings
import argparse
import configparser
import json

from collections import defaultdict
from py2neo import Graph

from mappers import MetaMapDriver


"""
This script performs all required mapping to existing terminologies
as specified in the iDISK schema. 
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts_file", type=str,
                        help="""Path to iDISK JSON lines file containing
                                concepts to map.""")
    parser.add_argument("--outfile", type=str,
                        help="Where to write the mapped JSON lines file.")
    parser.add_argument("--annotator_conf", type=str,
                        help="Path to config file for the annotators.")
    parser.add_argument("--uri", type=str, default="localhost",
                        help="URI of the graph to connect to.")
    parser.add_argument("--user", type=str, default="neo4j",
                        help="Neo4j username for this graph.")
    parser.add_argument("--password", type=str, default="password",
                        help="Neo4j password for this graph.")
    parser.add_argument("--schema_file", type=str, default=None,
                        help="""Path to schema.cypher.
                                If None, use existing graph at --uri.""")
    args = parser.parse_args()
    return args


class Schema(object):
    """
    The iDISK schema represented as a Neo4j graph.

    :param str uri: The URI for the graph.
    :param str user: The username for the graph.
    :param str pswd: The password for the graph.
    :param str cypher_file: Path to a Cypher file that defines the schema.
                            Optional. If not specified, use the existing graph.
    """

    def __init__(self, uri, user, pswd, cypher_file=None):
        self.graph = self._get_graph(uri, user, pswd)
        # Create the graph is a schema was specified.
        # Otherwise, use the existing graph at the uri.
        if cypher_file is not None:
            self._create_schema(cypher_file)
        else:
            if len(self.graph.nodes) == 0:
                raise AttributeError(f"Graph at URI '{uri}' is empty. Please specify a Cypher file.")  # noqa

    def _get_graph(self, uri, user, pswd):
        """
        Connect to the graph at uri with the specified credentials.

        :param str uri: The URI for the graph.
        :param str user: The username for the graph.
        :param str pswd: The password for the graph.
        :returns: The Neo4j graph.
        :rtype: py2neo.Graph
        """
        if uri.lower() == "localhost":
            uri = "bolt://localhost:7687"
        graph = Graph(uri, user=user, password=pswd)
        graph.begin()  # This will fail if there's a connection problem.
        return graph

    def _create_schema(self, cypher_file):
        """
        Creates a Neo4j graph as specified in cypher_file.

        :param str cypher_file: Path to a Cypher file that defines the schema.
        """
        if len(self.graph.nodes) > 0:
            raise ValueError(f"Cypher file specified but the graph is not empty. Aborting.")  # noqa
        cyp = open(cypher_file, 'r').read()
        self.graph.run(cyp)

    @property
    def external_terminologies(self):
        """
        Returns the terminologies that the concepts in the schema map to.

        :returns: Names of terminologies.
        :rtype: list
        """
        terms = set()
        for i in range(len(self.graph.nodes)):
            node = self.graph.nodes[i]
            if "maps_to" in node:
                terms.add(node["maps_to"])
        return terms

    def node_from_label(self, label):
        return self.graph.nodes.match(label).first()

    def rel_from_name(self, rel_name):
        return self.graph.relationships.match(r_type=rel_name).first()


def get_annotators(annotator_ini, schema):
    """
    Create instances of annotators for mapping
    concepts to existing terminologies.

    :param str annotator_ini: .ini file containing configuration parameters
                              for each annotation driver class.
    :param Schema schema: instance of Schema.
    :returns: annotators for each external database in the schema.
    :rtype: dict
    """

    annotator_map = {"umls": MetaMapDriver}
    external_dbs = schema.external_terminologies
    config = configparser.ConfigParser()
    config.read(annotator_ini)

    annotators = {}
    for db in external_dbs:
        if db not in annotator_map.keys():
            warnings.warn(f"No driver available for '{db}'. Skipping.")
            continue
        params = config[db]
        driver = annotator_map[db]
        annotators[db] = driver(**params)
    return annotators


def map_concepts(annotators, concepts_file, outfile, schema):
    with open(concepts_file, 'r') as inF:
        inlines = [json.loads(line) for line in inF]
    outlines = []

    # Build the queries to send to the annotators. Held in strings_to_map,
    # this will be a dict from a terminology to a tuple of an ID and a
    # string to map.
    counter = 0
    # 'UNK' for unknown source. We will use this later to know which
    # mappings to create new iDISK concepts for.
    counter_template = "UNK{0.07}"
    strings_to_map = defaultdict(list)
    for concept in inlines:
        cid = concept["id"]
        name = concept["preferred_term"]
        # TODO: Each concept should have a 'type' which specifies
        #       where it belongs in the schema. E.g.
        # terminology = schema.node_from_label(concept["type"])["maps_to"]
        concept_type = "SDSI"
        concept_terminology = schema.node_from_label(concept_type)["maps_to"]
        strings_to_map[concept_terminology].append((cid, name))

        for rel_json in concept["relationships"]:
            rel_name = rel_json["rel_name"]
            rel_graph = schema.rel_from_name(rel_name)
            if rel_graph.end_node() is None:
                warnings.warn(f"Relationship '{rel_name}' not in schema.")
                continue
            terminology = rel_graph.end_node()["maps_to"]
            string_id = counter_template.format(counter)
            string = rel_json["rel_value"]
            strings_to_map[terminology].append((string_id, rel_value))
            counter += 1

    # Run the annotators on their respective queries. The result of this step,
    # held in mappings, is a dictionary mapping string IDs to concepts.
    mappings = {}
    for terminology in strings_to_map.keys():
        query = '\n'.join([f"{sid}|{string}" for (sid, string)
                           in strings_to_map[terminology].items()])
        ann = annotators[terminology]
        candidates = ann.map(query)
        mappings[terminology] = ann.get_best_mappings(candidates)

    # TODO: Update MetaMapDriver's output to make it work with this.
    # Create new iDISK concepts for those mappings with an 'UNK' ID.
    num_syns = sum([len(c["synonyms"]) for c in inlines])
    idlib.Atom.init_counter(len(inlines) + num_syns)
    idlib.Concept.init_counter(len(inlines))
    for terminology in strings_to_map.keys():
        for (sid, mapping) in mappings[terminology].items():
            if not sid.startswith("UNK"):
                continue
            atom = idlib.Atom(orig_string, src, "", "SY", is_preferred=False)
            c = idlib.Concept(term=mapping["preferred_term"],
                              src=terminology, src_id=mapping["id"],
                              term_type="SY", is_preferred=True)


if __name__ == "__main__":
    raise Exception("This script is unfinished and should not be used.")
    args = parse_args()
    schema = Schema(args.uri, args.user, args.password,
                    cypher_file=args.schema_file)
    concepts = read_concepts(args.concepts_file)
    annotators = get_annotators(args.annotator_conf, schema)
    map_concepts(annotators, concepts, args.outfile, schema)
