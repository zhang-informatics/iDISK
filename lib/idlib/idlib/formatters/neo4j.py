import sys
import argparse
import logging
import datetime
import py2neo as p2n

from idlib.data_elements import Concept

logging.getLogger().setLevel(logging.INFO)
sys.setrecursionlimit(10000)

"""
Populate a Neo4j graph with the specified concepts.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts_file", type=str, required=True,
                        help="JSON lines file containing concepts.")
    # Neo4j graph access
    parser.add_argument("--uri", type=str, default="localhost",
                        help="URI of the graph to connect to.")
    parser.add_argument("--user", type=str, default="neo4j",
                        help="Neo4j username for this graph.")
    parser.add_argument("--password", type=str, default="password",
                        help="Neo4j password for this graph.")
    args = parser.parse_args()
    return args


def populate_neo4j_graph(graph, concepts):
    """
    Populate the Neo4j graph with the Concepts, Attributes,
    and Relationships present in concepts.

    :param py2neo.Graph graph: The graph database to populate.
    :param iterable concepts: The Concept instances.
    """

    def _convert_concept_to_node(concept):
        concept._prefix = "DC"
        attrs = {atr.atr_name: atr.atr_value
                 for atr in concept.get_attributes()}
        concept_node = p2n.Node(concept.concept_type,
                                ui=concept.ui,
                                name=concept.preferred_atom.term,
                                **attrs)
        return concept_node

    def _create_atom_nodes(concept):
        concept_node = ui_to_node[concept.ui]
        for atom in concept.get_atoms():
            atom._prefix = "DA"
            atom_node = p2n.Node(f"{concept.concept_type}_ATOM",
                                 ui=atom.ui,
                                 name=atom.term,
                                 src=atom.src,
                                 src_id=atom.src_id,
                                 is_preferred=atom.is_preferred,
                                 **atom.attrs)
            graph.create(
                    p2n.Relationship(concept_node,
                                     "has_synonym",
                                     atom_node)
                    )

    def _convert_relationship_to_edge(subject_node, relationship, object_node):
        relationship._prefix = "DR"
        attrs = {atr.atr_name: atr.atr_value
                 for atr in relationship.get_attributes()}
        return p2n.Relationship(subject_node,
                                relationship.rel_name,
                                object_node,
                                ui=relationship.ui,
                                src=relationship.src,
                                **attrs)

    def _add_concepts_to_graph(concept):
        """
        Perform a depth-first-search of this concept
        through its relationships.
        """
        try:
            return ui_to_node[concept.ui]
        except KeyError:
            pass
        concept_node = _convert_concept_to_node(concept)
        ui_to_node[concept.ui] = concept_node
        graph.create(concept_node)
        _create_atom_nodes(concept)
        for rel in concept.get_relationships():
            if isinstance(rel.object, Concept):
                obj_node = _add_concepts_to_graph(rel.object)
                rel_edge = _convert_relationship_to_edge(concept_node,
                                                         rel,
                                                         obj_node)
                graph.create(rel_edge)
        return concept_node

    ui_to_node = {}
    for (i, concept) in enumerate(concepts):
        if i % 1000 == 0:
            logging.info(f"{i}/{len(concepts)}")
        try:
            _add_concepts_to_graph(concept)
        except RecursionError:
            logging.error(f"Max recursion depth exceeded for {concept}.")
            raise RecursionError


# TODO: Figure out the best output format.
def export_to_graphml(graph, outfile):
    """
    Export the Neo4j graph to GraphML format.

    :param py2neo.Graph graph: The graph to export.
    :param str outdir: Where to save the output.
    """
    export_kwargs = '{useTypes:true, storeNodeIds:false}'
    apoc_call = f"CALL apoc.export.cypher.all('{outfile}', {export_kwargs})"
    graph.run(apoc_call)


if __name__ == "__main__":
    args = parse_args()

    logging.info(f"<neo4j> {str(datetime.datetime.now())}")
    logging.info(f"<neo4j> Connecting to graph at '{args.uri}'...")
    graph = p2n.Graph(host=args.uri, user=args.user, password=args.password)
    graph.begin()
    logging.info("<neo4j>  Success.")

    msg = f"<neo4j> Loading Concept instances from {args.concepts_file}."
    logging.info(msg)
    concepts = Concept.read_jsonl_file(args.concepts_file)

    logging.info(f"<neo4j> Populating graph.")
    populate_neo4j_graph(graph, concepts)
    logging.info(f"<neo4j> Done.")
