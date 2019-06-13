import argparse
import csv
import json

"""
Given a set of candidate connections and their annotations from Prodigy,
remove those candidate connections that did not get an 'Equal' label.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--connections_file", type=str, required=True,
                        help="""CSV file of connections, corresponding
                                to concepts_file.""")
    parser.add_argument("--annotations_file", type=str, required=True,
                        help="JSON lines file of annotated connections.")
    parser.add_argument("--outfile", type=str, required=True,
                        help="""Where to save the filtered connections
                                as JSON lines.""")
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


def read_annotations(infile):
    anns = []
    with open(infile, 'r') as inF:
        for line in inF:
            ann = json.loads(line)
            anns.append(ann)
    return anns


def filter_connections(connections, annotations):
    """
    Keep connections if they were assigned the 'Equal' label
    or if they were not annotated.

    :param list connections: List of candidate connections.
    :param list annotations: List of annotations from the
                             prodigy db-out command.
    :returns: Filtered connections.
    :rtype: list
    """
    # 1 corresponds to the equal label.
    annotated_idxs = [ann["_input_hash"] for ann in annotations]
    not_annotated_idxs = [i for i in range(len(connections))
                          if i not in annotated_idxs]
    equal_idxs = [ann["_input_hash"] for ann in annotations
                  if ann["answer"] == "accept" and 1 in ann["accept"]]
    keep_idxs = equal_idxs + not_annotated_idxs
    cnxs = [connections[i] for i in keep_idxs]
    return cnxs


def main(connections_file, annotations_file, outfile):
    candidate_cnxs = read_connections(connections_file)
    print(f"Number of candidate connections: {len(candidate_cnxs)}.")
    anns = read_annotations(annotations_file)
    filtered_cnxs = filter_connections(candidate_cnxs, anns)
    print(f"Number of filtered connections: {len(filtered_cnxs)}.")
    with open(outfile, 'w') as outF:
        writer = csv.writer(outF, delimiter=',')
        writer.writerows(filtered_cnxs)


if __name__ == "__main__":
    args = parse_args()
    main(args.connections_file, args.annotations_file, args.outfile)
