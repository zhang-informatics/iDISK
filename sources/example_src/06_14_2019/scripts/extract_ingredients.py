import argparse
import json
import re
import string
import pandas as pd

from idlib import Atom, Concept

"""
Formats ingredient information from NHP into the iDISK JSON lines
format.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--incsv", type=str, required=True,
                        help="""Input CSV file containing ingredient
                                information. E.g.
                                NHP_MEDICINAL_INGREDIENTS_fixed_ids.csv""")
    parser.add_argument("--outjsonl", type=str, required=True,
                        help="Where to save the output JSON lines file.")
    args = parser.parse_args()
    return args


def merge_duplicate_concepts(concepts):
    """
    NHP has many duplicate ingredients in the raw data. During
    data preprocessing each unique ingredient string is assigned a unique
    ID, so duplicate ingredient entries will have the same ID. This
    function merges those entries into a single concept.

    :param list concepts: List of Concept instances
    """

    def _merge(concept1, concept2):
        """
        Merges the atoms of concept2 into concept1, removing duplicates.
        This merge is performed in place.
        Luckily NHP concepts don't have attributes or relationships yet.
        so we don't have to merge those.
        """
        for atom in concept2.get_atoms():
            if atom not in concept1.get_atoms():
                concept1.atoms.append(atom)
        return concept1

    seen = {}  # {src_id: Concept}
    for concept in concepts:
        src_id = concept.preferred_atom.src_id
        if src_id not in seen:
            seen[src_id] = concept
        else:
            _merge(seen[src_id], concept)  # Changes seen[src_id] in place
    return seen.values()


def extract_ingredients(incsv, outjsonl):
    data = pd.read_csv(incsv, dtype=str)
    concepts = to_concepts(data)
    merged_concepts = merge_duplicate_concepts(concepts)
    with open(outjsonl, 'w') as outF:
        for concept in merged_concepts:
            json.dump(concept.to_dict(), outF)
            outF.write('\n')


def to_concepts(dataframe):
    Concept.set_ui_prefix("NHPID")

    dataframe = dataframe[["ingredient_id", "proper_name", "proper_name_f",
                           "common_name", "common_name_f"]].copy()
    dataframe.dropna(subset=["proper_name"], axis=0, inplace=True)
    dataframe.drop_duplicates(inplace=True)
    dataframe.fillna("", inplace=True)
    synonym_cols = ["proper_name_f", "common_name", "common_name_f"]

    seen = set()
    for row in dataframe.itertuples():
        row = row._asdict()
        pref_term = row["proper_name"]
        src_id = row["ingredient_id"]
        if invalid_ingredient(pref_term):
            print(f"Removing {pref_term}")
            continue

        pref_atom = Atom(term=pref_term, src="NHPID", src_id=src_id,
                         term_type="SN", is_preferred=True)
        atoms = [pref_atom]
        # Extract the synonyms, removing any empty strings
        # or duplicate string-termtype pairs.
        seen.add((pref_term, "SN"))
        for column in synonym_cols:
            term = row[column]
            tty = "SN" if column == "proper_name_f" else "SY"
            if not term:
                continue
            if (term, tty) in seen:
                continue
            seen.add((term, tty))
            atom = Atom(term=term, src="NHPID", src_id=row["ingredient_id"],
                        term_type=tty, is_preferred=False)
            atoms.append(atom)

        concept = Concept.from_atoms(atoms, concept_type="SDSI")
        yield concept


def invalid_ingredient(name):
    name = name.strip()
    # Just whitespace
    if not name:
        return True
    # Must be at least two characters
    if len(name) < 2:
        return True
    # Cannot be just a (decimal) number
    if re.match(r'^[.,]*[0-9]+[.,]*[0-9]+$', name):
        return True
    # Cannot be only punctuation
    if all([c in string.punctuation for c in name]):
        return True


if __name__ == "__main__":
    args = parse_args()
    extract_ingredients(args.incsv, args.outjsonl)
