import argparse
import csv
from tqdm import tqdm

from idlib import Concept

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
                raise ValueError("Improperly formatting CSV at line {i+1}.")
            cnx = [int(i) for i in row]
            cnxs.append(cnx)
    return cnxs


def filter_connections_same(connections, concepts):
    """
    Keep connections if the preferred_atom.term for
    both concepts is the same.

    :param list connections: List of candidate connections.
    :param list concepts: List of concepts.
    :returns: Filtered connections.
    :rtype: list
    """
    cnxs = []
    for (i, j) in connections:
        i_term = concepts[i].preferred_atom.term
        j_term = concepts[j].preferred_atom.term
        if i_term.lower() == j_term.lower():
            cnxs.append((i, j))
    return cnxs


def filter_connections_included(connections, concepts, ignore_concept_types):
    """
    Keep connections if the preferred_atom.term for
    one concept is in the atoms of the other concept.

    :param list connections: List of candidate connections.
    :param list concepts: List of concepts.
    :param list ignore_concept_types: List of concept types to exclude.
    :returns: Filtered connections.
    :rtype: list
    """
    cnxs = []
    for (i, j) in tqdm(connections):
        if concepts[i].concept_type.upper() in ignore_concept_types:
            continue
        i_pts = [a.term.lower() for a in concepts[i].get_atoms()
                 if a.is_preferred is True]
        i_terms = [a.term.lower() for a in concepts[i].get_atoms()]
        j_pts = [a.term.lower() for a in concepts[j].get_atoms()
                 if a.is_preferred is True]
        j_terms = [a.term.lower() for a in concepts[j].get_atoms()]

        if len(set(i_pts) & set(j_pts)) > 0:
            cnxs.append((i, j))
    return cnxs


def main(connections_file, concepts_file, outfile, ignore_concept_types):
    candidate_cnxs = read_connections(connections_file)
    print(f"Number of candidate connections: {len(candidate_cnxs)}.")
    concepts = Concept.read_jsonl_file(concepts_file)
    ignore_concept_types = [ct.upper() for ct in ignore_concept_types]
    print(f"Excluding concepts of types {ignore_concept_types}.")
    filtered_cnxs = filter_connections_included(candidate_cnxs, concepts,
                                                ignore_concept_types)
    print(f"Number of filtered connections: {len(filtered_cnxs)}.")
    with open(outfile, 'w') as outF:
        writer = csv.writer(outF, delimiter=',')
        writer.writerows(filtered_cnxs)


if __name__ == "__main__":
    args = parse_args()
    main(args.connections_file, args.concepts_file,
         args.outfile, args.ignore_concept_types)
