import argparse
import os

import pandas as pd


"""
Given a complete iDISK RRF build, computes the number of data elements coming
from each source.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rrf_dir", type=str, required=True,
                        help="""Directory containing RRF files.""")
    parser.add_argument("--outfile", type=str, required=True,
                        help="""Where to write the output.""")
    args = parser.parse_args()
    return args


def main(rrf_dir, outfile):
    conso_sty, rel, sat = read_rrf_files(rrf_dir)

    # Count concept types
    print("================")
    print("  CONCEPT TYPES")
    print("================")
    print(conso_sty["CUI"].unique().shape[0])
    print(conso_sty.drop_duplicates(subset="CUI")["STY"].value_counts())
    data = conso_sty.groupby(["STY", "CUI"])["SAB"].value_counts()
    data.name = "Counts"
    print(data.reset_index().groupby("STY")["SAB"].value_counts())
    print()

    print("================")
    print("  SDSI OVERLAP")
    print("================")
    sdsi = conso_sty[conso_sty["STY"] == "SDSI"]
    srcs = sdsi.groupby("CUI")["SAB"].apply(set).apply(sorted).apply('_'.join)
    print(srcs.str.replace("_UMLS", "").value_counts().sort_index())
    print()

    print("================")
    print(" RELATIONSHIPS")
    print("================")
    print(rel.shape[0])
    print(rel["REL"].value_counts().sort_index())
    print(rel.groupby(["REL"])["SAB"].value_counts())
    print()

    print("================")
    print("   ATTRIBUTES")
    print("================")
    print(sat.shape[0])
    print(sat["ATN"].value_counts().sort_index())
    print(sat.groupby(["ATN"])["SAB"].value_counts())
    print()


def read_rrf_files(rrf_dir):
    conso_file = os.path.join(rrf_dir, "MRCONSO.RRF")
    sty_file = os.path.join(rrf_dir, "MRSTY.RRF")
    rel_file = os.path.join(rrf_dir, "MRREL.RRF")
    sat_file = os.path.join(rrf_dir, "MRSAT.RRF")

    conso = pd.read_csv(conso_file, dtype=str, sep='|')
    sty = pd.read_csv(sty_file, dtype=str, sep='|')
    conso_sty = conso.merge(sty, on="CUI")

    rel = pd.read_csv(rel_file, dtype=str, sep='|')
    sat = pd.read_csv(sat_file, dtype=str, sep='|')

    return conso_sty, rel, sat


if __name__ == "__main__":
    args = parse_args()
    main(args.rrf_dir, args.outfile)
