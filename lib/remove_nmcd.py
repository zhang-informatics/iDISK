import argparse
import json
from tqdm import tqdm

from idlib import Concept


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts_file", type=str, required=True)
    parser.add_argument("--outfile", type=str, required=True)
    args = parser.parse_args()
    return args


def remove_nmcd(concepts):

    def _check_for_nmcd(concept, concepts_to_rm):
        if concept in concepts_to_rm:
            return True
        nmcd_atoms = [a for a in concept.get_atoms() if a.src == "NMCD"]
        concept.rm_elements(nmcd_atoms)
        if len(concept._atoms) == 0:
            return True
        return False

    concepts_to_rm = set()
    for concept in tqdm(concepts):
        if _check_for_nmcd(concept, concepts_to_rm) is True:
            concepts_to_rm.add(concept)
            continue

        to_rm = []
        for atr in concept.get_attributes():
            if atr.src == "NMCD":
                to_rm.append(atr)

        for rel in concept.get_relationships():
            if rel.src == "NMCD":
                to_rm.append(rel)
                continue
            if _check_for_nmcd(rel.object, concepts_to_rm) is True:
                concepts_to_rm.add(rel.object)
                to_rm.append(rel)

            for relatr in rel.get_attributes():
                if relatr.src == "NMCD":
                    rel.rm_elements(relatr)

        concept.rm_elements(to_rm)

    return (c for c in concepts if c not in concepts_to_rm)


if __name__ == "__main__":
    args = parse_args()
    print("Loading Concepts")
    concepts = Concept.read_jsonl_file(args.concepts_file)
    concepts = remove_nmcd(concepts)
    with open(args.outfile, 'w') as outF:
        for concept in concepts:
            json.dump(concept.to_dict(), outF)
            outF.write('\n')
