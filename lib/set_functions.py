import argparse
import json
import copy

from collections import defaultdict


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
    result = func(iter1, iter2)
    with open(outfile, 'w') as outF:
        for line in result:
            json.dump(line, outF)
            outF.write('\n')


def intersection(iter1, iter2):
    """
    Given two iterators of iDISK JSON objects containing ingredient names,
    computes their intersection, matching on both the 'preferred_term'
    field and the 'synonyms' field.

    Parameters:
    iter1: List of JSON objects in the iDISK JSON format.
    iter2: List of JSON objects in the iDISK JSON format.

    Returns:
    List of JSON objects representing terms that were found
    in both list1 and list2.
    """
    seen = set()
    matched = defaultdict(bool)  # default False
    intersection_terms = []
    for ing1 in iter1:
        for ing2 in iter2:
            overlap = match(ing1, ing2)
            if len(overlap) > 0:
                matched[ing1["preferred_term"]] = True
                ing1 = merge(ing1, ing2)
        if matched[ing1["preferred_term"]] is True:
            if ing1["preferred_term"] not in seen:
                intersection_terms.append(ing1)
                seen.add(ing1["preferred_term"])
    return intersection_terms


def union(iter1, iter2):
    """
    Given two iterators of iDISK JSON objects containing ingredient names,
    computes their union, matching on both the 'preferred_term'
    field and the 'synonyms' field.

    Parameters:
    iter1: List of JSON objects in the iDISK JSON format.
    iter2: List of JSON objects in the iDISK JSON format.

    Returns:
    List of JSON objects representing terms that were found
    in iter1, iter2, as well as in both iter1 and iter2.
    """
    seen = set()
    matched = defaultdict(bool)  # default False
    union_terms = []
    for ing1 in iter1:
        for ing2 in iter2:
            overlap = match(ing1, ing2)
            if len(overlap) > 0:
                if matched[ing2["preferred_term"]] is False:
                    ing1 = merge(ing1, ing2)
                    matched[ing2["preferred_term"]] = True
        if ing1["preferred_term"] not in seen:
            seen.add(ing1["preferred_term"])
            union_terms.append(ing1)

    unmatched_terms = [ing for ing in iter2 if
                       matched[ing["preferred_term"]] is False]
    union_terms = union_terms + unmatched_terms
    return union_terms


def difference(iter1, iter2):
    """
    Given two iterators of iDISK JSON objects containing ingredient names,
    compute their difference, matching on both the 'preferred_term'
    field and the 'synonyms' field.

    Parameters:
    iter1: List of JSON objects in the iDISK JSON format.
    iter2: List of JSON objects in the iDISK JSON format.

    Returns:
    List of JSON objects representing terms that were found
    in iter1 and iter2, but not both.
    """
    matched = defaultdict(bool)  # default False
    for ing1 in iter1:
        for ing2 in iter2:
            overlap = match(ing1, ing2)
            if len(overlap) > 0:
                matched[ing1["preferred_term"]] = True
                matched[ing2["preferred_term"]] = True
    difference_terms = [ing for ing in iter1+iter2
                        if matched[ing["preferred_term"]] is False]
    return difference_terms


def match(ing1, ing2):
    """
    Finds the overlap of synonyms between two ingredient terms.

    Parameters:
    ing1: JSON object in the iDISK JSON format.
    ing2: JSON object in the iDISK JSON format.

    Returns:
    set() of terms that were found in both ingredient name lists.
    """
    ing1_names = [syn["term"].lower() for syn in ing1["synonyms"]]
    ing1_names.append(ing1["preferred_term"].lower())
    ing2_names = [syn["term"].lower() for syn in ing2["synonyms"]]
    ing2_names.append(ing2["preferred_term"].lower())
    overlap = set(ing1_names).intersection(set(ing2_names))
    return overlap


def merge(ing1, ing2):
    """
    Merges the second ingredient into the first by concatenating their
    synonyms (adding the second ingredients preferred term into the synonym
    list), and taking the union of their attributes and relationships.

    Parameters:
    ing1: JSON object in the iDISK JSON format.
    ing2: JSON object in the iDISK JSON format.

    Returns:
    JSON object in iDISK JSON format of ing2 merged into ing1.
    """
    merged = copy.deepcopy(ing1)
    pref_name_syn = {"term": ing2["preferred_term"],
                     "src": ing2["src"],
                     "src_id": ing2["src_id"],
                     "term_type": ing2["term_type"],
                     "is_preferred": True}

    # Merge synonyms, removing duplicates
    if ing2["synonyms"] != []:
        for syn in ing2["synonyms"] + [pref_name_syn]:
            if syn not in merged["synonyms"]:
                merged["synonyms"].append(syn)

    # Merge attributes, removing duplicates
    if ing2["attributes"] != []:
        for attr in ing2["attributes"]:
            if attr not in merged["attributes"]:
                merged["attributes"].append(attr)

    # Merge relationships, removing duplicates
    if ing2["relationships"] != []:
        for rel in ing2["relationships"]:
            if rel not in merged["relationships"]:
                merged["relationships"].append(rel)

    return merged


if __name__ == "__main__":
    func_table = {"intersection": intersection,
                  "union": union,
                  "difference": difference}
    args = parse_args()
    perform_set_function(func_table[args.set_function],
                         args.ingredients1, args.ingredients2,
                         args.outfile)
