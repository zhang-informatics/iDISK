import sys
import argparse
import logging
import configparser
import json
from collections import defaultdict

from mappers import MetaMapDriver
from idlib import Schema, Atom, Concept, Attribute


"""
This script performs all required mapping to existing terminologies
as specified in the iDISK schema.
"""

logging.getLogger().setLevel(logging.INFO)


class LinkedString(object):
    """
    A LinkedString is a single str some substring or substrings of
    which can be linked to an external terminology. For example,

    "... is helpful for headaches and toothaches"

    has two mappable substrings: "headaches" and "toothaches".
    These correspond to CandidateLink instances and are assigned
    to the candidate_links attribute of this class.

    Each LinkedString has an ID corresponding the hash of the full input
    string, accessed by `LinkedString().id`.

    :param str string: The full string to try to link.
    :param str concept_type: The iDISK concept_type of the resulting linkings.
    :param str terminology: The external terminology to link to.
    :param list candidate_links: (Optional) List of CandidateLink instances
                                 derived from string.
    """
    def __init__(self, string, concept_type,
                 terminology, id=None, candidate_links=None):
        self.string = string
        self.concept_type = concept_type
        self.terminology = terminology
        self.candidate_links = candidate_links or []
        self._id = id

    def __repr__(self):
        return str(self.__dict__)

    def __str(self):
        return str(self.__dict__)

    @property
    def id(self):
        if self._id is None:
            self._id = str(hash(self.string) % sys.maxsize)
        return self._id

    @id.setter
    def id(self, value):
        self._id = value


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
            logging.warning(f"No driver available for '{db}'. Skipping.")
            continue
        params = config[db]
        driver = annotator_map[db]
        annotators[db] = driver(**params)
    return annotators


def get_linkables_from_concepts(concepts, schema):
    """
    Create a LinkedString instance for each concept with a maps_to
    attribute in the schema.

    :param iterable concepts: The concepts to search within.
    :param Schema schema: The iDISK schema.
    :returns: Set of LinkedString instances without the
              candidate_links attribute.
    :rtype: list
    """
    linkables = []
    for concept in concepts:
        concept_node = schema.get_node_from_label(concept.concept_type)
        try:
            concept_terminology = concept_node["maps_to"]
        except KeyError:
            continue
        linkable = LinkedString(string=concept.preferred_atom.term,
                                terminology=concept_terminology,
                                id=concept.ui,
                                concept_type=list(concept_node.labels)[0])
        linkables.append(linkable)
    return linkables


def get_linkables_from_relationships(concepts, schema):
    """
    For each concept, find all strings that are to be linked
    to an external terminology. Create a Linking instance for
    each string, and replace it in the concept with a unique
    string ID, which will later be used to determine which
    newly created concept will be placed in its stead.

    :param iterable concepts: The concepts to search within.
    :param Schema schema: The iDISK schema.
    :returns: Set of Linking instances without the candidate_links attribute.
    :rtype: list
    """
    linkables = []
    for concept in concepts:
        for rel in concept.get_relationships():
            rel_graph = schema.get_relationship_from_name(rel.rel_name)
            if rel_graph is None:
                msg = f"Relationship {rel.rel_name} is not in the schema."
                logging.warning(msg)
                continue
            rel_terminology = rel_graph.end_node["maps_to"]
            if rel_terminology is None:
                # We aren't supposed to link this.
                continue
            concept_type = list(rel_graph.end_node.labels)[0]
            linkable = LinkedString(string=rel.object,
                                    terminology=rel_terminology,
                                    concept_type=concept_type)
            linkables.append(linkable)
            rel.object = linkable.id
    return linkables


def link_entities(linkables, annotators):
    """
    Link the Linking.string instances to external terminologies using
    annotators.

    :param iterable linkings: Linking instances to link.
    :param dict annotators: Dictionary from source database names
                            to EntityLinker instances.
    :returns: The input Linking instances with their
              candidate_links values populated.
    :rtype: list
    """
    # TODO: Come up with a definitive list and put it in a config file.
    valid_semtypes = {"SDSI": ["vita", "phsu", "clnd", "plnt", "orch"],
                      "DIS": ["dsyn", "inbe"],
                      "SPD": ["phsu", "clnd"],
                      }

    linkables_by_id = {l.id: l for l in linkables}

    # Build the queries to send to each terminology.
    queries_by_terminology = defaultdict(list)
    # Used to restrict the possible entities for a query.
    keep_semtypes_by_terminology = defaultdict(dict)
    for i in range(len(linkables)):
        terminology = linkables[i].terminology
        lid = linkables[i].id
        concept_type = linkables[i].concept_type
        semtypes = valid_semtypes.get(concept_type)
        string = linkables[i].string
        if semtypes is not None:
            keep_semtypes_by_terminology[terminology][lid] = semtypes
        query = f"{lid}|{string}"
        queries_by_terminology[terminology].append(query)

    # Run each query.
    for (terminology, queries) in queries_by_terminology.items():
        try:
            ann = annotators[terminology]
        except KeyError:
            continue
        keep_semtypes = keep_semtypes_by_terminology[terminology]
        candidates = ann.link(queries, keep_semtypes=keep_semtypes)
        candidates = ann.get_best_links(candidates)

        # Add the linked entities to the corresponding Linking instance.
        # {LinkedString().id: [[CandidateLink], [...]]}
        for (lid, cand_link) in candidates.items():
            if cand_link is None:
                continue
            linkable = linkables_by_id[lid]
            linkable.candidate_links.append(cand_link)

    return linkables


def add_linkings_to_existing_concepts(linked_strs, existing_concepts):
    """
    Given a set of Linking instances and existing concepts, create an
    Atom for each CandidateLink that linked from an existing concept and
    add it to the concept. Also add any attributes associated with the
    CandidateLink as attributes of the concept.

    :param iterable linked_strs: LinkedString instances to create concepts for.
    :param iterable existing_concepts: Already existing concepts.
    :returns: Updated set of concepts.
    :rtype: list
    """
    num_existing_atoms = sum([1 for concept in existing_concepts
                              for atom in concept.get_atoms()])
    Atom.init_counter(num_existing_atoms)
    Concept.init_counter(len(existing_concepts))

    concept_lookup = {c.ui: c for c in existing_concepts}

    for linked_str in linked_strs:
        if linked_str.candidate_links == []:
            continue
        try:
            concept = concept_lookup[linked_str.id]
        except KeyError:
            continue
        for cand in linked_str.candidate_links:
            mapped_str_atom = Atom(cand.candidate_term,
                                   src=cand.candidate_source,
                                   src_id=cand.candidate_id,
                                   term_type="SY",
                                   is_preferred=True)
            concept.add_elements(mapped_str_atom)
            for (atr_name, atr_values) in cand.attrs.items():
                if isinstance(atr_values, str):
                    atr_values = [atr_values]
                for val in atr_values:
                    concept.add_elements(
                            Attribute(subject=concept,
                                      atr_name=atr_name,
                                      atr_value=val,
                                      src=linked_str.terminology.upper())
                            )
    return existing_concepts


def create_concepts_from_linkings(linked_strs, existing_concepts):
    """
    This function creates Concept instances for those Relationship objects
    that were successfully linked and updates the Relationship objects to
    be the newly created Concepts.

    :param iterable linked_strs: LinkedString instances to create concepts for.
    :param iterable existing_concepts: Already existing concepts.
    :returns: Updated set of concepts.
    :rtype: list
    """

    num_existing_atoms = sum([1 for concept in existing_concepts
                              for atom in concept.get_atoms()])
    Atom.init_counter(num_existing_atoms)
    Concept.init_counter(len(existing_concepts))

    existing_concept_uis = [c.ui for c in existing_concepts]

    # Create the Concepts for each entity linked from each Relationship object.
    # Each Concept has two Atoms, one for the original string, and one for the
    # linked entity.
    new_concepts_by_id = {}
    for linked_str in linked_strs:
        if linked_str.candidate_links == []:
            continue
        if linked_str.id in existing_concept_uis:
            continue
        for cand in linked_str.candidate_links:
            orig_str_atom = Atom(linked_str.string,
                                 src="IDISK",
                                 src_id=linked_str.id,
                                 term_type="SY",
                                 is_preferred=False)
            mapped_str_atom = Atom(cand.candidate_term,
                                   src=cand.candidate_source,
                                   src_id=cand.candidate_id,
                                   term_type="SY",
                                   is_preferred=True)
            new_concept = Concept(concept_type=linked_str.concept_type,
                                  atoms=[orig_str_atom, mapped_str_atom])
            matched_atr = Attribute(subject=new_concept,
                                    atr_name="mapped_from_orig_str",
                                    atr_value=cand.input_string,
                                    src="IDISK")
            new_concept.add_elements(matched_atr)
            new_concept._prefix = cand.candidate_source

            # Incorporate any attributes from the links into the Concept.
            for (atr_name, atr_values) in cand.attrs.items():
                if isinstance(atr_values, str):
                    atr_values = [atr_values]
                for val in atr_values:
                    new_concept.add_elements(
                            Attribute(subject=new_concept,
                                      atr_name=atr_name,
                                      atr_value=val,
                                      src=linked_str.terminology.upper())
                            )

            new_concepts_by_id[linked_str.id] = new_concept

    # Modify all the Relationships' objects to be the corresponding
    # Concept created above.
    already_warned = set()
    linked_strs_by_id = {ls.id: ls for ls in linked_strs}
    for concept in existing_concepts:
        for rel in concept.get_relationships():
            rel_graph = schema.get_relationship_from_name(rel.rel_name)
            linkable = rel_graph.end_node["maps_to"] is not None
            if not linkable:
                continue
            try:
                obj_concept = new_concepts_by_id[rel.object]
            except KeyError:
                str_id = rel.object
                orig_string = linked_strs_by_id[str_id].string
                rel.object = orig_string
                if str_id not in already_warned:
                    msg = f"{str_id} ({orig_string}) was not linked."
                    logging.warning(msg)
                    already_warned.add(str_id)
                continue
            rel.object = obj_concept

    return existing_concepts + list(new_concepts_by_id.values())


def link_concepts(concepts, annotators, schema):
    concept_linkables = get_linkables_from_concepts(concepts, schema)
    linkings = link_entities(concept_linkables, annotators)
    concepts = add_linkings_to_existing_concepts(linkings, concepts)
    return concepts


def link_relationship_objects(concepts, annotators, schema):
    rel_linkables = get_linkables_from_relationships(concepts, schema)
    linkings = link_entities(rel_linkables, annotators)
    concepts = create_concepts_from_linkings(linkings, concepts)
    return concepts


if __name__ == "__main__":
    args = parse_args()
    # Load the Neo4j schema
    schema = Schema(args.uri, args.user, args.password,
                    cypher_file=args.schema_file)
    # Load in the Concept instances
    concepts = Concept.read_jsonl_file(args.concepts_file)
    # Load the annotators, e.g. MetaMap.
    annotators = get_annotators(args.annotator_conf, schema)
    # Link the Concept instances to existing terminologies,
    # and add any relevant attributes.
    concepts = link_concepts(concepts, annotators, schema)
    # Create Concept instances for the objects of all Relationships
    # belonging to the existing Concepts, and update the Relationship
    # objects accordingly.
    concepts = link_relationship_objects(concepts, annotators, schema)
    with open(args.outfile, 'w') as outF:
        for concept in concepts:
            json.dump(concept.to_dict(), outF)
            outF.write('\n')
