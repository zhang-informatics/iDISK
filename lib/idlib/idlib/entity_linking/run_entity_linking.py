import os
import sys
import argparse
import logging
import importlib
import json
from collections import defaultdict

import idlib


"""
This script performs all required mapping to existing terminologies
as specified in the iDISK schema.
"""

logging.getLogger().setLevel(logging.INFO)


class LinkedString(object):
    """
    A LinkedString is a single string, some substring or substrings of
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
    def __init__(self, string, src, concept_type,
                 terminology, id=None, candidate_links=None):
        self.string = string
        self.src = src
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
    # Input and output files
    parser.add_argument("--concepts_file", type=str, required=True,
                        help="""Path to iDISK JSON lines file containing
                                concepts to map.""")
    parser.add_argument("--outfile", type=str, required=True,
                        help="Where to write the mapped JSON lines file.")
    # Annotator settings
    parser.add_argument("--linkers_conf", type=str, required=True,
                        help="Path to config file for the entity linkers.")
    parser.add_argument("--keep_top_n", type=int, default=1,
                        help="Keep the N best links for each candidate.")
    # Schema access
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


def get_linkers(linkers_conf, schema):
    """
    Create instances of entity linkers for mapping
    concepts to existing terminologies.

    :param str linkers_conf: JSON file containing configuration parameters
                              for each entity linker driver class.
    :param Schema schema: instance of Schema.
    :returns: linkers for each external database in the schema.
    :rtype: dict
    """
    # Import the linkers dynamically according to the "class_name"
    # attribute in linkers.conf.
    linkers_module = importlib.import_module("idlib.entity_linking.linkers")

    if not os.path.exists(linkers_conf):
        raise OSError("{linkers_conf} not found.")
    config = json.load(open(linkers_conf, 'r'))

    external_dbs = schema.external_terminologies
    logging.info("Starting entity linkers")
    linkers = {}
    for db in external_dbs:
        params = config[db]
        # This will throw an AttributeError if the class_name
        # is not in the linkers module.
        driver = getattr(linkers_module, params["class_name"])
        params.update({"name": db})
        del params["class_name"]
        linkers[db] = (driver, params)
    return linkers


def get_linkables_from_concepts(concepts, schema):
    """
    Create a LinkedString instance for each concept with a links_to
    attribute in the schema.

    :param iterable concepts: The concepts to search within.
    :param Schema schema: The iDISK schema.
    :returns: Set of LinkedString instances without the
              candidate_links attribute.
    :rtype: list
    """
    seen = set()
    linkables = []
    for concept in concepts:
        concept_node = schema.get_node_from_label(concept.concept_type)
        concept_terminology = concept_node["links_to"]
        if concept_terminology is None:
            continue
        linkable = LinkedString(string=concept.preferred_atom.term,
                                src=concept.preferred_atom.src,
                                terminology=concept_terminology,
                                id=concept.ui,
                                concept_type=list(concept_node.labels)[0])
        if linkable.id not in seen:
            seen.add(linkable.id)
            linkables.append(linkable)
    return list(linkables)


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
    already_warned = set()
    seen = set()
    linkables = []
    for concept in concepts:
        for rel in concept.get_relationships():
            rel_graph = schema.get_relationship_from_name(rel.rel_name)
            if rel_graph is None:
                if rel.rel_name not in already_warned:
                    already_warned.add(rel.rel_name)
                    msg = f"Relationship {rel.rel_name} is not in the schema."
                    logging.warning(msg)
                continue
            rel_terminology = rel_graph.end_node["links_to"]
            if rel_terminology is None:
                # We aren't supposed to link this.
                continue
            concept_type = list(rel_graph.end_node.labels)[0]
            linkable = LinkedString(string=rel.object,
                                    terminology=rel_terminology,
                                    concept_type=concept_type)
            if linkable.id not in seen:
                seen.add(linkable.id)
                linkables.append(linkable)
            rel.object = linkable.id
    return list(linkables)


def link_entities(linkables, linkers, keep_top_n):
    """
    Link the Linking.string instances to external terminologies using
    linkers.

    :param iterable linkings: Linking instances to link.
    :param dict linkers: Dictionary from source database names
                            to EntityLinker instances.
    :param int keep_top_n: Keep the top N concepts linked.
    :returns: The input Linking instances with their
              candidate_links values populated.
    :rtype: list
    """
    # Make it so we can look up each LinkedString instance by its ID.
    linkables_by_id = {l.id: l for l in linkables}

    # Build the queries to send to each terminology.
    queries_by_terminology = defaultdict(list)
    # Used to restrict the possible entities for a query.
    for linkable in linkables:
        terminology = linkable.terminology
        lid = linkable.id
        string = linkable.string
        query = (lid, string)
        queries_by_terminology[terminology].append(query)

    # Run each query.
    for (terminology, queries) in queries_by_terminology.items():
        try:
            driver, params = linkers[terminology]
            linker = driver(**params)
        except KeyError:
            continue
        # candidates is a dictionary of the format
        # {LinkedString.id: {matched_input: [CandidateLink, [...]]}}
        candidates = linker.link(queries)
        # This just filters the list of CandidateLinks to keep the top N.
        candidates = linker.get_best_links(candidates, keep_top_n=keep_top_n)

        # Add the linked entities to the corresponding Linking instance.
        total = 0
        for lid in candidates.keys():
            for cand_links in candidates[lid].values():
                # if cand_link is None:
                if cand_links == []:
                    continue
                total += 1
                linkable = linkables_by_id[lid]
                linkable.candidate_links.append(cand_links)
        # Destroy this driver. Required for QuickUMLS, but good in
        # all cases to ensure we're not keeping unnecessary things
        # in memory.
        del linker

    return linkables


def create_concepts_from_linkings(linkings, existing_concepts):
    """
    Given a set of Linking instances and existing concepts, create a new
    Concept for each CandidateLink. Also add any attributes associated with
    the CandidateLink as attributes of the concept.

    :param iterable linked_strs: LinkedString instances to create concepts for.
    :param iterable existing_concepts: Already existing concepts.
    :returns: Updated set of concepts.
    :rtype: list
    """
    max_atom = max([atom._number for concept in existing_concepts
                    for atom in concept.get_atoms()])
    idlib.data_elements.Atom.init_counter(max_atom)
    max_concept = max([concept._number for concept in existing_concepts])
    idlib.data_elements.Concept.init_counter(max_concept)

    concept_lookup = {c.ui: c for c in existing_concepts}

    new_concepts = []
    old2new_concepts = defaultdict(list)
    for (i, linked_str) in enumerate(linkings):
        if i % 500 == 0:
            logging.info(f"{i}/{len(linkings)}")
        # "umls.metamap" -> "UMLS"
        link_src = linked_str.terminology.split('.')[0].upper()
        if linked_str.candidate_links == []:
            try:
                existing_concepts.remove(concept_lookup[linked_str.id])
            except ValueError:
                pass
            continue
        try:
            old_concept = concept_lookup[linked_str.id]
        except KeyError:
            continue
        # For each candidate linking...
        for (i, candidates) in enumerate(linked_str.candidate_links):
            # Create a Concept for this link
            new_concept = idlib.data_elements.Concept.from_concept(old_concept)
            # Add data elements corresponding to each linking.
            for cand in candidates:
                mapped_str_atom = idlib.data_elements.Atom(
                        cand.candidate_term,
                        src=cand.candidate_source,
                        src_id=cand.candidate_id,
                        term_type="SY",
                        is_preferred=True,
                        linked_string=cand.input_string,
                        linking_score=cand.linking_score)
                new_concept.add_elements(mapped_str_atom)

                # Add any other attributes from the CandidateLink,
                # such as the UMLS semantic types, etc.
                for (atr_name, atr_values) in cand.attrs.items():
                    if not isinstance(atr_values, (list, set)):
                        atr_values = [atr_values]
                    for val in atr_values:
                        new_concept.add_elements(
                                idlib.data_elements.Attribute(
                                    subject=new_concept,
                                    atr_name=atr_name,
                                    atr_value=val,
                                    src=link_src)
                                )
            new_concepts.append(new_concept)

            old2new_concepts[old_concept.ui].append(new_concept)
            # Delete the original concept that we mapped from.
            # TODO: I can't figure out why existing_concepts.remove(concept)
            # doesn't work. `concept in existing_concepts` returns True.
            existing_concepts = [c for c in existing_concepts
                                 if c != old_concept]

    # Update the relationships for all the concepts.
    all_concepts = existing_concepts + new_concepts
    for concept in all_concepts:
        to_add = []
        to_rm = []
        for rel in concept.get_relationships():
            try:
                new_concepts = old2new_concepts[rel.object.ui]
            except KeyError:
                continue
            for nc in new_concepts:
                new_rel = idlib.data_elements.Relationship.from_relationship(rel)  # noqa
                new_rel.object = nc
                to_add.append(new_rel)
            to_rm.append(rel)
        concept.add_elements(to_add)
        concept.rm_elements(to_rm)

    return all_concepts


def link_concepts(concepts, linkers, schema, keep_top_n=1):
    linker_names = [linker[1]["name"] for linker in linkers.values()]
    logging.info(f"Entity Linkers: {linker_names}")
    logging.info("LINKING CONCEPTS")
    concept_linkables = get_linkables_from_concepts(concepts, schema)
    logging.info(f"Number of linkables: {len(concept_linkables)}.")
    linkings = link_entities(concept_linkables, linkers, keep_top_n)
    logging.info("Creating new concepts from linkings.")
    concepts = create_concepts_from_linkings(linkings, concepts)
    logging.info("COMPLETE")
    return concepts


if __name__ == "__main__":
    args = parse_args()
    # Load the Neo4j schema
    schema = idlib.Schema(args.uri, args.user, args.password,
                          cypher_file=args.schema_file)
    # Load in the Concept instances
    logging.info("Loading Concepts.")
    concepts = idlib.read_jsonl_file(args.concepts_file)
    # Load the linkers, e.g. MetaMap.
    linkers = get_linkers(args.linkers_conf, schema)
    if linkers == []:
        raise ValueError("No linkers found. Check your schema.")
    # Link the Concept instances to existing terminologies,
    # and add any relevant attributes.
    concepts = link_concepts(concepts, linkers, schema,
                             keep_top_n=args.keep_top_n)
    # Create Concept instances for the objects of all Relationships
    # belonging to the existing Concepts, and update the Relationship
    # objects accordingly.
    logging.info(f"Saving concepts to {args.outfile}")
    with open(args.outfile, 'w') as outF:
        for concept in concepts:
            json.dump(concept.to_dict(), outF)
            outF.write('\n')
