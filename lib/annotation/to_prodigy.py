import argparse
import csv
import json

from idlib import Concept


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concepts_file", type=str, required=True,
                        help="""iDISK JSON lines file containing
                                all concepts.""")
    parser.add_argument("--connections_file", type=str, required=True,
                        help="""CSV file containing indices of connections
                                in concepts_file.""")
    parser.add_argument("--outfile", type=str, required=True,
                        help="Where to save the output file.")
    args = parser.parse_args()
    return args


def read_connections_file(infile):
    cnxs = []
    with open(infile, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for (i, row) in enumerate(reader):
            if len(row) != 2:
                raise ValueError("Improperly formatted row at line {i+1}.")
            cnxs.append([int(i) for i in row])
    return cnxs


def read_concepts_file(infile):
    concepts = []
    with open(infile, 'r') as inF:
        for (i, line) in enumerate(inF):
            data = json.loads(line)
            concept = Concept.from_dict(data)
            concepts.append(concept)
    return concepts


def convert_all_to_prodigy(concepts, connections):
    for (i, j) in connections:
        ci = concepts[i]
        cj = concepts[j]
        prodigy_json = convert_one_to_prodigy(ci, cj)
        yield prodigy_json


def convert_one_to_prodigy(concept1, concept2):
    c1_terms = [a.term.lower() for a in concept1.get_atoms()]
    c2_terms = [a.term.lower() for a in concept2.get_atoms()]
    overlap = set(c1_terms).intersection(set(c2_terms))
    pref1 = concept1.preferred_atom
    pref2 = concept2.preferred_atom
    outjson = {"ing1": {"term": pref1.term,
                        "src": pref1.src,
                        "src_id": pref1.src_id},
               "ing2": {"term": pref2.term,
                        "src": pref2.src,
                        "src_id": pref2.src_id},
               "matched_on": sorted(overlap)}
    return outjson


def main(concepts_file, connections_file, outfile):
    print("Reading concepts...", end='', flush=True)
    concepts = read_concepts_file(concepts_file)
    print("Done", flush=True)
    cnxs = read_connections_file(connections_file)
    with open(outfile, 'w') as outF:
        for outjson in convert_all_to_prodigy(concepts, cnxs):
            json.dump(outjson, outF)
            outF.write('\n')


if __name__ == "__main__":
    args = parse_args()
    main(args.concepts_file, args.connections_file, args.outfile)
