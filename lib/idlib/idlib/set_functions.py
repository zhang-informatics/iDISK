import argparse
import json
import csv
import copy
from tqdm import tqdm, trange  # Progress bar

from idlib import Concept


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("function", type=str,
                        choices=["intersection", "union", "difference",
                                 "find_connections"],
                        help="The set function to perform.")
    parser.add_argument("--infiles", type=str, nargs='+', required=True,
                        help="""JSON lines files containing
                                the lists of concepts.""")
    parser.add_argument("--outfile", type=str, required=True,
                        help="Where to save the result.")
    parser.add_argument("--connections_file", type=str, default=None,
                        help="""CSV file containing pairs of indices of
                                connected concepts in the input, one pair
                                per line. Assumes that the concepts have
                                already been concatenated and thus there
                                is only one infile.""")
    args = parser.parse_args()
    return args


def read_connections_file(infile):
    """
    Reads a two-column CSV file of integers into a list of tuples
    corresponding to indices of connected concepts.

    :param str infile: Path to the CSV file.
    :returns: List of int tuples of connections.
    :rtype: list
    """
    connections = []
    with open(infile, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            assert(len(row) == 2)
            row = [int(i) for i in row]
            connections.append(tuple(row))
    return connections


def perform_find_connections(outfile, *infiles):
    """
    Run find_connections without the set function and write the result
    outfile.

    :param str outfile: The path to the outfile.
    :param list infiles: A list of paths to the concept files.
    """
    all_concepts = []
    for fpath in infiles:
        data = [json.loads(line) for line in open(fpath, 'r')]
        concepts = [Concept.from_dict(d) for d in data]
        all_concepts.extend(concepts)
    print(f"Number of starting concepts: {len(all_concepts)}")
    cnxs = Union(all_concepts, run_union=False).connections
    with open(outfile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(cnxs)


def perform_set_function(func, outfile, *infiles, connections=None):
    """
    Run find_connections without the set function and write the result
    outfile.

    :param Union outfile: The set function to run.
    :param str outfile: The path to the outfile.
    :param list infiles: A list of paths to the concept files.
    :param list connections: List of int tuples specifying connections.
    """
    all_concepts = []
    for fpath in infiles:
        data = [json.loads(line) for line in open(fpath, 'r')]
        concepts = [Concept.from_dict(d) for d in data]
        all_concepts.extend(concepts)
    print(f"Number of starting concepts: {len(all_concepts)}")
    result = func(all_concepts, connections=connections).result
    print(f"Number of resulting concepts: {len(result)}")
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


class Union(object):
    """
    An implementation of the union-find datastructure specific for
    iDISK Concepts.

    The routine starts by finding connections between pairs of concepts
    in the input. It then merges the connected concepts, always mergin the
    concept with fewer number of atoms into the concept with the greater.

    This class can be used to generate a list of candidate connections,
    which can then be filtered, by passing ``run_union=False`` and then
    getting the ``connections`` attribute. Once filtered, they can be passed
    back in as the ``connections`` argument with ``run_union=True``.

    See the idlib README for example usage.

    :param list concepts: One or more lists of Concept instances.
    :param list connections: A list of int tuples specifying connections
                             between pairs of concepts, where each int
                             in a given tuple is the index of the concept
                             in the concepts argument. Optional. If not
                             provided, pairs of concepts are connected if
                             they share one or more atom terms.
    :param bool run_union: If True (default) run union-find on the input.
                           Otherwise, just run find_connections.
    """
    def __init__(self, concepts, connections=[], run_union=True):
        self._check_params(concepts, connections)
        self.concepts = concepts
        self.concepts_map = dict(enumerate(self.concepts))
        self.parents_map = dict(enumerate(range(len(self.concepts))))
        if connections == []:
            print(f"Finding connections...")
            self.connections = self.find_connections()
        else:
            self.connections = connections
        print(f"Number of connections: {len(self.connections)}")
        if run_union is True:
            self.union_find()
            self.result = [self.concepts_map[i]
                           for i in set(self.parents_map.values())]

    def _check_params(self, concepts, connections):
        assert(all([isinstance(c, Concept) for c in concepts]))
        assert(isinstance(connections, list))
        if len(connections) > 0:
            assert(all([isinstance(elem, tuple) for elem in connections]))
            assert(all([isinstance(i, int) for elem in connections
                        for i in elem]))

    def _connected(self, i, j):
        """
        Two concepts are connected if they share one or more atoms.

        :param int i: The index of the first concept.
        :param int j: The index of the second concept.
        :returns: Whether concepts i and j are connected.
        :rtype: bool
        """
        ci = self.concepts_map[i]
        cj = self.concepts_map[j]
        ci_terms = [a.term for a in ci.get_atoms()]
        cj_terms = [a.term for a in cj.get_atoms()]
        overlap = set(ci_terms).intersection(set(cj_terms))
        return len(overlap) > 0

    def find_connections(self):
        """
        Finds all pairs of concepts that share one or more atom
        terms. Returns connections as a list of int tuples.

        :returns: connections
        :rtype: list
        """
        connections = []
        for i in trange(len(self.concepts_map)):
            for j in range(i+1, len(self.concepts_map)):
                if self._connected(i, j):
                    connections.append((i, j))
        return connections

    def _merge(self, concept_i, concept_j):
        """
        Merges the second Concepts into the first by merging their Atoms,
        Attributes, and Relationships.

        :param Concept concept_i: The first concept.
        :param Concept concept_j: The second concept.
        :returns: Merged concept.
        :rtype: Concept
        """
        merged = copy.deepcopy(concept_i)
        # Replace the prefix
        new_prefix = _get_prefix(concept_i, concept_j)
        merged._prefix = new_prefix
        # Merge atoms, removing duplicates.
        for atom in concept_j.get_atoms():
            if atom not in merged.atoms:
                merged.atoms.append(atom)

        # Merge attributes, removing duplicates and changing the subject.
        for atr in concept_j.get_attributes():
            if atr not in merged.attributes:
                atr.subject = merged
                merged.attributes.append(atr)

        # Merge relationships, removing duplicates and changing the subject.
        for rel in concept_j.get_relationships():
            if rel not in merged.relationships:
                rel.subject = merged
                for a in rel.attributes:
                    a.subject = merged
                merged.relationships.append(rel)
        return merged

    def _find(self, i):
        """
        The find operation of union-find with path compression.

        :param int i: The index of the concept whose root to find.
        :returns: The root of concept i
        :rtype: int
        """
        if i != self.parents_map[i]:  # If this is not a root node
            self.parents_map[i] = self._find(self.parents_map[i])
        return self.parents_map[i]

    def _union(self, i, j):
        """
        The union operation of union-find. Merges concepts with fewer
        atoms into those with more.

        :param int i: The index of the first concept to merge.
        :param int j: The index of the second concept to merge.
        """
        pi = self._find(i)
        pj = self._find(j)
        if pi == pj:
            return
        concept_i = self.concepts_map[pi]
        concept_j = self.concepts_map[pj]
        # Merge the smaller concept into the bigger.
        if len(concept_i.atoms) < len(concept_j.atoms):
            pi, pj = pj, pi
            concept_i, concept_j = concept_j, concept_i
        # Merge concept_j into concept_i
        self.concepts_map[pi] = self._merge(concept_i, concept_j)
        self.parents_map[pj] = pi

    def union_find(self):
        """
        The union-find routine. Given a list of connections, merges them.
        """
        for (i, j) in tqdm(self.connections):
            self._union(i, j)


class Intersection(Union):
    """
    The intersection of a list of concepts is the set of all those concepts
    that are matched to one or more other concepts.

    :param list concepts: One or more lists of Concept instances.
    :param list connections: A list of int tuples specifying connections
                             between pairs of concepts, where each int
                             in a given tuple is the index of the concept
                             in the concepts argument. Optional. If not
                             provided, pairs of concepts are connected if
                             they share one or more atom terms.
    """
    def __init__(self, concepts, connections=[]):
        super().__init__(concepts, connections, run_union=True)
        parent_idxs = [v for (k, v) in self.parents_map.items() if k != v]
        self.result = [self.concepts_map[i] for i in set(parent_idxs)]


class Difference(Union):
    """
    The difference of a list of concepts is the set of all those concepts
    that could not be matched to at least one other concept.

    :param list concepts: One or more lists of Concept instances.
    :param list connections: A list of int tuples specifying connections
                             between pairs of concepts, where each int
                             in a given tuple is the index of the concept
                             in the concepts argument. Optional. If not
                             provided, pairs of concepts are connected if
                             they share one or more atom terms.
    """
    def __init__(self, concepts, connections=[]):
        super().__init__(concepts, connections, run_union=True)
        # The unmatched concepts correspond to those indices that only occur
        # once in parents_map
        from collections import Counter
        idx_counts = Counter(self.parents_map.values())
        parent_idxs = [k for (k, v) in idx_counts.items() if v == 1]
        # and which have no parent
        parent_idxs = [k for k in parent_idxs if k == self.parents_map[k]]
        self.result = [self.concepts_map[i] for i in parent_idxs]


if __name__ == "__main__":
    func_table = {"union": Union,
                  "intersection": Intersection,
                  "difference": Difference}
    args = parse_args()
    cnxs = []

    if args.connections_file is not None:
        cnxs = read_connections_file(args.connections_file)

    if args.function == "find_connections":
        # Just find connections, don't compute the union.
        perform_find_connections(args.outfile, *args.infiles)
    else:
        func = func_table[args.function]
        perform_set_function(func, args.outfile, *args.infiles,
                             connections=cnxs)
