import argparse
import csv
import numpy as np
from tqdm import tqdm
from collections import defaultdict

from idlib.data_elements import Concept

"""
Given a set of candidate connections and the concepts,
remove those candidate connections whose corresponding concepts
do not have the same preferred term.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--connections_file", type=str, required=True,
                        help="""CSV file of connections, corresponding
                                to concepts_file.""")
    parser.add_argument("--concepts_file", type=str, required=True,
                        help="JSON lines file of concepts.")
    parser.add_argument("--outfile", type=str, required=True,
                        help="""Where to save the filtered connections
                                as JSON lines.""")
    parser.add_argument("--ignore_concept_types", nargs='*',
                        help="List of concept types to automatically exclude.")
    args = parser.parse_args()
    return args


def read_connections(infile):
    cnxs = []
    with open(infile, 'r') as inF:
        reader = csv.reader(inF, delimiter=',')
        for (i, row) in enumerate(reader):
            if len(row) != 2:
                raise ValueError("Improperly formatted CSV at line {i+1}.")
            cnx = [int(i) for i in row]
            cnxs.append(cnx)
    return cnxs


def filter_connections(connections, concepts, ignore_concept_types):
    """
    Keep connections if the preferred_atom.term for
    one concept is in the atoms of the other concept.

    :param list connections: List of candidate connections.
    :param list concepts: List of concepts.
    :param list ignore_concept_types: List of concept types to exclude.
    :returns: Filtered connections.
    :rtype: list
    """
    what_happen = {"no_linked": 0, "linked": 0}
    cnxs = []
    for (i, j) in tqdm(connections):

        if concepts[i].concept_type.upper() in ignore_concept_types:
            continue

        i_terms = []
        i_pts = []
        i_linked_terms = []
        for a in concepts[i].get_atoms():
            i_terms.append(a.term.lower())
            if a.is_preferred is True:
                if "linking_score" in a.attrs.keys():
                    i_linked_terms.append(a.term.lower())
                else:
                    i_pts.append(a.term.lower())

        j_terms = []
        j_pts = []
        j_linked_terms = []
        for a in concepts[j].get_atoms():
            j_terms.append(a.term.lower())
            if a.is_preferred is True:
                if "linking_score" in a.attrs.keys():
                    j_linked_terms.append(a.term.lower())
                else:
                    j_pts.append(a.term.lower())

        if len(i_linked_terms) == 0 or len(j_linked_terms) == 0:
            if len(set(i_terms) & set(j_pts)) > 0 or len(set(j_pts) & set(j_terms)) > 0:  # noqa
                what_happen["no_linked"] += 1
                cnxs.append((i, j))
        else:
            num_atoms = min([len(set(i_linked_terms)), len(set(j_linked_terms))])  # noqa
            keep = int(np.ceil(num_atoms * 1.00))
            if len(set(i_linked_terms) & set(j_linked_terms)) >= keep:
                what_happen["linked"] += 1
                cnxs.append((i, j))
    print(what_happen)

    return cnxs


def filter_connections_idf(connections, concepts, ignore_concept_types):
    """
    Keep connections if the preferred_atom.term for
    one concept is in the atoms of the other concept.

    :param list connections: List of candidate connections.
    :param list concepts: List of concepts.
    :param list ignore_concept_types: List of concept types to exclude.
    :returns: Filtered connections.
    :rtype: list
    """
    idfs = linked_idf(concepts)
    idf_range = max(idfs.values()) - min(idfs.values())
    threshold = min(idfs.values()) + (idf_range / 1.5)
    print(max(idfs.values()), min(idfs.values()))
    print(threshold)
    what_happen = {"no_linked": 0, "linked": 0}
    cnxs = []
    for (i, j) in tqdm(connections):

        if concepts[i].concept_type.upper() in ignore_concept_types:
            continue

        i_terms = []
        i_pts = []
        i_linked_terms = []
        for a in concepts[i].get_atoms():
            i_terms.append(a.term.lower())
            if a.is_preferred is True:
                if "linking_score" in a.attrs.keys():
                    if idfs[a.src_id] >= threshold:
                        i_linked_terms.append(a.term.lower())
                else:
                    i_pts.append(a.term.lower())

        j_terms = []
        j_pts = []
        j_linked_terms = []
        for a in concepts[j].get_atoms():
            j_terms.append(a.term.lower())
            if a.is_preferred is True:
                if "linking_score" in a.attrs.keys():
                    if idfs[a.src_id] >= threshold:
                        j_linked_terms.append(a.term.lower())
                else:
                    j_pts.append(a.term.lower())

        if len(i_linked_terms) == 0 or len(j_linked_terms) == 0:
            #if len(set(i_terms) & set(j_pts)) > 0 or len(set(j_pts) & set(j_terms)) > 0:  # noqa
            if len(set(i_pts) & set(j_pts)) > 0:
                what_happen["no_linked"] += 1
                cnxs.append((i, j))
        else:
            num_atoms = min([len(set(i_linked_terms)), len(set(j_linked_terms))])  # noqa
            if len(set(i_linked_terms) & set(j_linked_terms)) > 1:
                what_happen["linked"] += 1
                cnxs.append((i, j))
    print(what_happen)

    return cnxs


def linked_idf(concepts):
    df = defaultdict(int)
    for concept in concepts:
        linked_ids = set([a.src_id for a in concept.get_atoms()
                          if "linking_score" in a.attrs.keys()])
        for lid in linked_ids:
            df[lid] += 1
    idf = {lid: np.log(len(concepts)/freq) for (lid, freq) in df.items()}
    return idf


def main(connections_file, concepts_file, outfile, ignore_concept_types):
    candidate_cnxs = read_connections(connections_file)
    print(f"Number of candidate connections: {len(candidate_cnxs)}.")
    concepts = Concept.read_jsonl_file(concepts_file)
    ignore_concept_types = [ct.upper() for ct in ignore_concept_types]
    print(f"Excluding concepts of types {ignore_concept_types}.")
    filtered_cnxs = filter_connections(candidate_cnxs, concepts,
                                       ignore_concept_types)
    print(f"Number of filtered connections: {len(filtered_cnxs)}.")
    with open(outfile, 'w') as outF:
        writer = csv.writer(outF, delimiter=',')
        writer.writerows(filtered_cnxs)


if __name__ == "__main__":
    args = parse_args()
    main(args.connections_file, args.concepts_file,
         args.outfile, args.ignore_concept_types)
