import argparse
import configparser
from py2neo import Graph


class Schema(object):
    """
    The iDISK schema represented as a Neo4j graph.

    :param str uri: The URI for the graph. E.g. "bolt://localhost:7687".
    :param str user: The username for the graph.
    :param str password: The password for the graph.
    :param str cypher_file: Path to a Cypher file that defines the schema.
                            Optional. If not specified, use the existing graph.
    """

    def __init__(self, uri, user, password, cypher_file=None):
        self.graph = self._get_graph(uri, user, password)
        # Create the graph if a schema was specified.
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
            msg = "Cypher file specified but the graph is not empty. Aborting."
            raise ValueError(msg)
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
        for node_record in self.graph.run("MATCH (n) RETURN (n)"):
            node = node_record["n"]
            if "links_to" in node:
                terms.add(node["links_to"])
        return terms

    def get_node_from_label(self, label):
        """
        :param str label: The label to use as a lookup.
        """
        return self.graph.nodes.match(label.upper()).first()

    def get_relationship_from_name(self, rel_name):
        """
        :param str rel_name: The relationship name.
        """
        return self.graph.relationships.match(r_type=rel_name.upper()).first()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema_version", type=str, required=True,
                        help="""The version number (such as 1.0.0)
                                of this schema.""")
    parser.add_argument("--schema_conf_file", type=str, required=True,
                        help=".ini configuration file for this schema.")
    args = parser.parse_args()
    return args


def build_schema(schema_version, schema_conf_file):
    config = configparser.ConfigParser()
    config.read(schema_conf_file)
    schema_config = config[schema_version]
    schema = Schema(uri=schema_config["uri"],
                    user=schema_config["user"],
                    password=schema_config["password"],
                    cypher_file=schema_config["cypher_file"])
    print(schema.graph)


if __name__ == "__main__":
    args = parse_args()
    build_schema(args.schema_version, args.schema_conf_file)
