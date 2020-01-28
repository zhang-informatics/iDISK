import argparse
import logging
import json
import csv
import copy
from itertools import combinations
from tqdm import tqdm  # Progress bar

import idlib

logging.getLogger().setLevel(logging.INFO)


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
    parser.add_argument("--ignore_concept_types", type=str, nargs="*",
                        help="""A list of concept types to ignore when
                                checking for a match.""")
    args = parser.parse_args()
    return args


def read_concepts_files(*infiles):
    """
    Read in the Concepts from the infiles.

    :param list infiles: A list of paths to the concept files.
    :returns: List of Concepts.
    :rtype: list
    """
    all_concepts = []
    for fpath in infiles:
        concepts = idlib.read_jsonl_file(fpath)
        all_concepts.extend(concepts)
    return all_concepts


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


def perform_find_connections(concepts, outfile, ignore_concept_types=[]):
    """
    Run find_connections without the set function and write the result
    outfile.

    :param list concepts: A list of Concepts to run over.
    :param list outfile: Where to save the output.
    """
    cnxs = Union(concepts, run_union=False,
                 ignore_concept_types=ignore_concept_types).connections
    with open(outfile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerows(cnxs)
    logging.info("Done")


def perform_set_function(func, concepts, outfile, connections=None,
                         ignore_concept_types=[]):
    """
    Run find_connections without the set function and write the result
    outfile.

    :param Union func: The set function to run.
    :param list concepts: A list of Concepts to run over.
    :param str outfile: The path to the outfile.
    :param list connections: List of int tuples specifying connections.
    """
    result = func(concepts, connections=connections,
                  ignore_concept_types=ignore_concept_types).result
    logging.info(f"Number of resulting concepts: {len(result)}")
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
    def __init__(self, concepts, connections=None, run_union=True,
                 ignore_concept_types=None):
        self.concepts = concepts
        self.connections = connections or []
        self.ignore_concept_types = ignore_concept_types or []
        self._check_params(self.concepts, self.connections,
                           self.ignore_concept_types)

        if len(self.ignore_concept_types) > 0:
            logging.info(f"Ignoring types: {self.ignore_concept_types}.")

        self.ui2index = {c.ui: i for (i, c) in enumerate(self.concepts)}
        self.parents = list(range(len(self.concepts)))
        if self.connections == []:
            logging.info("Finding connections...")
            self.connections = self.find_connections()
        if run_union is True:
            self.union_find()
            self.result = self.update_relationships()

    def _check_params(self, concepts, connections, ignore_types):
        assert(all([isinstance(c, idlib.data_elements.Concept)
                    for c in concepts]))
        assert(isinstance(connections, list))
        if len(connections) > 0:
            assert(all([isinstance(elem, tuple) for elem in connections]))
            assert(all([isinstance(i, int) for elem in connections
                        for i in elem]))
        assert(isinstance(ignore_types, list))
        if len(ignore_types) > 0:
            assert(all([isinstance(elem, str) for elem in ignore_types]))

    def find_connections(self):
        """
        Finds all pairs of concepts that share one or more atom
        terms. Returns connections as a generator over int tuples.

        :returns: A generator over connections [i, j]
        :rtype: Generator
        """

        def _cache_atoms(indices):
            # Cache the atoms of each concept to speed things up.
            cache = {i: set([a.term.lower()
                             for a in self.concepts[i].get_atoms()])
                     for i in indices}
            return cache

        def _cache_concept_types(indices):
            # Cache the types of each concept to speed things up.
            cache = {i: self.concepts[i].concept_type for i in indices}
            return cache

        def _filter_indices(idxs):
            # Remove indices of concepts that should be ignored.
            filtered_idxs = []
            for i in idxs:
                if _type_cache[i] in self.ignore_concept_types:
                    continue
                filtered_idxs.append(i)
            return filtered_idxs

        def _connected(i, j):
            # Two concepts are connected if their atoms overlap.
            ci_type = _type_cache[i]
            cj_type = _type_cache[j]
            if ci_type != cj_type:
                return False
            ci_terms = _atom_cache[i]
            cj_terms = _atom_cache[j]
            overlap = ci_terms.intersection(cj_terms)
            return bool(overlap)

        idxs = list(range(len(self.concepts)))
        _type_cache = _cache_concept_types(idxs)
        idxs = _filter_indices(idxs)
        _atom_cache = _cache_atoms(idxs)

        combos = combinations(idxs, 2)
        # This is a quick approximation as the factorials get large.
        n_combos = (len(idxs)**2 // 2) - len(idxs)
        n_connections = 0
        for (count, (i, j)) in enumerate(combos):
            if count % 1000000 == 0:
                logging.info(f"{count}/{n_combos} : # cnxs {n_connections}")
            if _connected(i, j) is True:
                n_connections += 1
                yield (i, j)

        logging.info(f"# cnxs {n_connections}")

    def _merge(self, concept_i, concept_j):
        """
        Merges the second Concepts into the first by merging their Atoms,
        Attributes, and Relationships.

        :param Concept concept_i: The first concept.
        :param Concept concept_j: The second concept.
        :returns: Merged concept.
        :rtype: Concept
        """
        merged = copy.copy(concept_i)
        # Replace the prefix
        new_prefix = _get_prefix(concept_i, concept_j)
        merged._prefix = new_prefix

        # Merge atoms.
        merged.add_elements(concept_j.get_atoms())

        # Merge attributes, changing the subject.
        for atr in concept_j.get_attributes():
            atr.subject = merged
            merged.add_elements(atr)

        # Merge relationships, removing duplicates and changing the subject.
        for rel in concept_j.get_relationships():
            rel.subject = merged
            for a in rel.get_attributes():
                a.subject = merged
            merged.add_elements(rel)
        return merged

    def _find(self, i):
        """
        The find operation of union-find with path compression.

        :param int i: The index of the concept whose root to find.
        :returns: The root of concept i
        :rtype: int
        """
        if i != self.parents[i]:  # If this is not a root node
            self.parents[i] = self._find(self.parents[i])
        return self.parents[i]

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
        concept_i = self.concepts[pi]
        concept_j = self.concepts[pj]
        # Merge the smaller concept into the bigger.
        if len(concept_i._atoms) < len(concept_j._atoms):
            pi, pj = pj, pi
            concept_i, concept_j = concept_j, concept_i
        # Merge concept_j into concept_i
        merged = self._merge(concept_i, concept_j)
        self.concepts[pi] = merged
        self.ui2index[merged.ui] = pi
        self.parents[pj] = pi

    def union_find(self):
        """
        The union-find routine. Given a list of connections, merges them.
        """
        for (i, j) in tqdm(self.connections):
            self._union(i, j)

    def update_relationships(self):
        # Make sure we find the parent of any concepts we did not
        # update in _union.
        _ = [self._find(i) for i in range(len(self.concepts))]
        concepts = [self.concepts[i] for i in set(self.parents)]
        for concept in concepts:
            for rel in concept.get_relationships():
                try:
                    object_idx = self.ui2index[rel.object.ui]
                except AttributeError:
                    continue
                parent_idx = self.parents[object_idx]
                parent_concept = self.concepts[parent_idx]
                rel.object = parent_concept
        return concepts


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
        parent_idxs = [c for (i, c) in enumerate(self.parents) if i != c]
        self.result = [self.concepts[i] for i in set(parent_idxs)]


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
        idx_counts = Counter(self.parents)
        parent_idxs = [k for (k, v) in idx_counts.items() if v == 1]
        # and which have no parent
        parent_idxs = [k for k in parent_idxs if k == self.parents[k]]
        self.result = [self.concepts[i] for i in parent_idxs]


if __name__ == "__main__":
    func_table = {"union": Union,
                  "intersection": Intersection,
                  "difference": Difference}
    args = parse_args()

    logging.info("Loading concepts.")
    concepts = read_concepts_files(*args.infiles)
    logging.info(f"Number of starting concepts: {len(concepts)}")

    cnxs = []
    if args.connections_file is not None:
        cnxs = read_connections_file(args.connections_file)

    if args.function == "find_connections":
        # Just find connections, don't compute the union.
        perform_find_connections(concepts, args.outfile,
                                 ignore_concept_types=args.ignore_concept_types)  # noqa
    else:
        func = func_table[args.function]
        perform_set_function(func, concepts, args.outfile, connections=cnxs,
                             ignore_concept_types=args.ignore_concept_types)
