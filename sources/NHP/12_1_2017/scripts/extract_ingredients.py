import argparse
import json
import re
import string
import pandas as pd


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


def extract_ingredients(incsv, outjsonl):
    data = pd.read_csv(incsv, dtype=str)
    lines = format_as_jsonl(data)
    with open(outjsonl, 'w') as outF:
        for line in lines:
            json.dump(line, outF)
            outF.write('\n')


def format_as_jsonl(dataframe):
    dataframe = dataframe[["ingredient_id", "proper_name", "proper_name_f",
                           "common_name", "common_name_f"]].copy()
    dataframe.dropna(subset=["proper_name"], axis=0, inplace=True)
    dataframe.drop_duplicates(inplace=True)
    dataframe.fillna("", inplace=True)

    synonym_cols = ["proper_name_f", "common_name", "common_name_f"]
    seen_terms = set()
    for row in dataframe.itertuples():
        row = row._asdict()
        pref_name = row["proper_name"]
        # Check if the ingredient name isn't nonsense.
        # NHP contains names like '1000' and '%'.
        if invalid_ingredient(pref_name):
            print(f"Removing {pref_name}")
            continue

        # Extract the synonyms, removing any empty strings
        # or duplicate string-termtype pairs.
        seen_terms.add((pref_name, "SN"))
        synonyms = []
        for column in synonym_cols:
            syn = get_synonym(row, column)
            if syn is None:
                continue
            if (syn["term"], syn["term_type"]) in seen_terms:
                continue
            seen_terms.add((syn["term"], syn["term_type"]))
            synonyms.append(syn)

        json_line = {"preferred_term": pref_name,
                     "src": "NHPID",
                     "src_id": row["ingredient_id"],
                     "term_type": "SN",
                     "synonyms": synonyms,
                     "attributes": [],
                     "relationships": []
                     }
        yield json_line


def get_synonym(row, column):
    term = row[column]
    if not term:
        return None
    term_type = "SN" if column == "proper_name_f" else "SY"
    synonym = {"term": term, "src": "NHPID",
               "src_id": row["ingredient_id"],
               "term_type": term_type, "is_preferred": False}
    return synonym


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
