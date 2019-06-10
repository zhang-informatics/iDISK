import argparse
import json
import copy

from collections import defaultdict

from idlib import Concept


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("set_function", type=str,
                        choices=["intersection", "union", "difference"],
                        help="The set function to perform.")
    parser.add_argument("ingredients1", type=str,
                        help="File containing the first list of ingredients.")
    parser.add_argument("ingredients2", type=str,
                        help="File containing the second list of ingredients.")
    parser.add_argument("outfile", type=str, help="Where to save the result.")
    args = parser.parse_args()
    return args


def perform_set_function(func, file1, file2, outfile):
    iter1 = [json.loads(line) for line in open(file1, 'r')]
    iter2 = [json.loads(line) for line in open(file2, 'r')]
    concepts1 = [Concept.from_dict(d) for d in iter1]
    concepts2 = [Concept.from_dict(d) for d in iter2]
    result = func(concepts1, concepts2)
    with open(outfile, 'w') as outF:
        for concept in result:
            json.dump(concept.to_dict(), outF)
            outF.write('\n')


def _get_prefix(concept1, concept2):
    """
    Build a  Concept UI prefix as the combination of the
    UI prefixes of two concepts.

    :param Concept concept1: The first concept.
    :param Concept concept2: The second concept.
    :returns: New prefix
    :rtype: str
    """
    # ["NMCD_NMCD", "DSLD_NHP"]
    prefixes = [concept1._prefix, concept2._prefix]
    # "NMCD_NMCD_DSLD_NHP"
    prefixes = '_'.join(prefixes)
    # {"NMCD", "DSLD", "NHP"}
    srcs = set([src for src in prefixes.split('_')])
    # "NMCD_DSLD_NHP"
    merged_prefix = '_'.join(srcs)
    return merged_prefix


def intersection(concepts1, concepts2):
    """
    Given two lists of Concepts, computes their intersection,
    matching on their atoms. Concepts that match are merged.

    :param list(Concept) concepts1: First list of concepts.
    :param list(Concept) concepts2: Second list of concepts.
    :returns: List of merged concepts common to both lists.
    :rtype: list(Concept)
    """
    # Set the prefix for any merged concepts.
    prefix = _get_prefix(concepts1[0], concepts2[0])
    Concept.set_ui_prefix(prefix)

    matched = defaultdict(bool)  # default False
    intersection_concepts = []

    for c1 in concepts1:
        c_new = copy.deepcopy(c1)
        for c2 in concepts2:
            overlap = match(c1, c2)
            if len(overlap) > 0:
                matched[c1.ui] = True
                c_new = merge(c_new, c2)
        if matched[c1.ui] is True:
            intersection_concepts.append(c_new)
    return intersection_concepts


def union(concepts1, concepts2):
    """
    Given two lists of Concepts computes their union, matching on their atoms.
    Concepts that match are merged.

    :param list(Concept) concepts1: First list of concepts.
    :param list(Concept) concepts2: Second list of concepts.
    :returns: The union.
    :rtype: list(Concept)
    """
    # Set the prefix for any merged concepts.
    prefix = _get_prefix(concepts1[0], concepts2[0])
    Concept.set_ui_prefix(prefix)

    matched_pairs = []
    matched_c2 = defaultdict(bool)
    union_concepts = []
    for c1 in concepts1:
        c_new = None
        for c2 in concepts2:
            if c1 == c2:
                continue
            if set([c1.ui, c2.ui]) in matched_pairs:
                continue
            overlap = match(c1, c2)
            if len(overlap) > 0:
                matched_c2[c2.ui] = True
                matched_pairs.append(set([c1.ui, c2.ui]))
                if c_new is None:
                    # Create a new concept with the merged prefix.
                    c_new = Concept(c1.concept_type, atoms=c1.atoms,
                                    attributes=c1.attributes,
                                    relationships=c1.relationships)
                c_new = merge(c_new, c2)
        if c_new is not None:
            union_concepts.append(c_new)
    print(len(union_concepts))
    unmatched_concepts = [c for c in concepts2 if matched_c2[c.ui] is False]
    union_concepts += unmatched_concepts
    return union_concepts


def difference(concepts1, concepts2):
    """
    Given two lists of Concepts, compute their difference,
    matching on their atoms.

    :param list(Concept) concepts1: First list of concepts.
    :param list(Concept) concepts2: Second list of concepts.
    :returns: List of concepts that were found in concepts1 and concepts2,
              but not both.
    :rtype: list(Concept)
    """
    matched = defaultdict(bool)
    for c1 in concepts1:
        for c2 in concepts2:
            overlap = match(c1, c2)
            if len(overlap) > 0:
                matched[c1.ui] = True
                matched[c2.ui] = True
    all_concepts = concepts1 + concepts2
    diff_terms = [c for c in all_concepts if matched[c.ui] is False]
    return diff_terms


def match(concept1, concept2):
    """
    Finds the atom overlap between two concepts.

    :param Concept concept1: The first concept.
    :param Concept concept2: The second concept.
    :returns: set of atoms that were found in both concepts.
    :rtype: set(Atom)
    """
    c1_terms = [a.term for a in concept1.get_atoms()]
    c2_terms = [a.term for a in concept2.get_atoms()]
    overlap = set(c1_terms).intersection(set(c2_terms))
    return overlap


def merge(concept1, concept2):
    """
    Merges the second ingredient into the first by merging their atoms,
    attributes, and relationships.

    :param Concept concept1: The first concept.
    :param Concept concept2: The second concept.
    :returns: A single concept resulting from merging the two input concepts.
    :rtype: Concept
    """
    merged = copy.deepcopy(concept1)

    # Merge atoms, removing duplicates.
    for atom in concept2.get_atoms():
        if atom not in merged.atoms:
            merged.atoms.append(atom)

    # Merge attributes, removing duplicates.
    for atr in concept2.get_attributes():
        if atr not in merged.attributes:
            merged.attributes.append(atr)

    # Merge relationships, removing duplicates.
    for rel in concept2.get_relationships():
        if rel not in merged.relationships:
            merged.relationships.append(rel)

    return merged


if __name__ == "__main__":
    func_table = {"intersection": intersection,
                  "union": union,
                  "difference": difference}
    args = parse_args()
    perform_set_function(func_table[args.set_function],
                         args.ingredients1, args.ingredients2,
                         args.outfile)
