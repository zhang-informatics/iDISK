import argparse
import pandas as pd

"""
Since the NHPID data does not include ingredient IDs,
adds dummy IDs to NHPID ingredients according to proper_name.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--incsv", type=str, required=True,
                        help="NHP_MEDICINAL_INGREDIENTS_fixed.csv")
    parser.add_argument("--outcsv", type=str, required=True,
                        help="Where to save the output.")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    csvdata = pd.read_csv(args.incsv)
    names = csvdata.proper_name.unique()
    ids = [f"{i:04}" for i in range(1, names.shape[0] + 1)]
    names2ids = dict(zip(names, ids))
    id_col = [names2ids[name] for name in csvdata.proper_name]
    csvdata.insert(0, "ingredient_id", id_col)
    csvdata.to_csv(args.outcsv, header=True, index=False)


if __name__ == "__main__":
    main()
