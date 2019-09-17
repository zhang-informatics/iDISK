import argparse
import json
from tqdm import tqdm

from idlib import Concept


"""
Deletes all atoms, attributes, and relationships
from the specified source. If all of a concept's atoms
are deleted, it is deleted as well.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts_file", type=str, required=True,
                        help="The JSON lines file containing the concepts.")
    parser.add_argument("--source_code", type=str, required=True,
                        help="The source code of the data to remove.")
    parser.add_argument("--outfile", type=str, required=True,
                        help="Where to save the result.")
    args = parser.parse_args()
    return args


def remove_source(concepts, source_code):
    """
    :param list concepts: List of Concept instances to search through.
    :param str source_code: The source code of the data to delete.
    :returns: List of Concept instances with the source_code data deleted.
    :rtype: list
    """

    def _remove_atoms(concept, concepts_to_rm):
        if concept in concepts_to_rm:
            return True
        atoms_to_rm = [a for a in concept.get_atoms() if a.src == source_code]
        concept.rm_elements(atoms_to_rm)

    concepts_to_rm = set()
    for concept in tqdm(concepts):
        _remove_atoms(concept, concepts_to_rm)
        if len(concept._atoms) == 0:
            concepts_to_rm.add(concept)
            continue

        to_rm = []
        for atr in concept.get_attributes():
            if atr.src == source_code:
                to_rm.append(atr)

        for rel in concept.get_relationships():
            if rel.src == source_code:
                to_rm.append(rel)
                continue
            _remove_atoms(rel.object, concepts_to_rm)
            if len(rel.object._atoms) == 0:
                concepts_to_rm.add(rel.object)
                to_rm.append(rel)

            for relatr in rel.get_attributes():
                if relatr.src == source_code:
                    rel.rm_elements(relatr)

        concept.rm_elements(to_rm)

    return (c for c in concepts if c not in concepts_to_rm)


if __name__ == "__main__":
    args = parse_args()
    print("Loading Concepts...")
    concepts = Concept.read_jsonl_file(args.concepts_file)
    print("Done")
    source_code = args.source_code.upper()
    concepts = remove_source(concepts, source_code)
    with open(args.outfile, 'w') as outF:
        for concept in concepts:
            json.dump(concept.to_dict(), outF)
            outF.write('\n')
