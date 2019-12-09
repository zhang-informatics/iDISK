import argparse
import os

import pandas as pd

from scipy.stats import skew, kurtosis


"""
Given a complete iDISK RRF build, computes the number of data elements coming
from each source.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rrf_dir", type=str, required=True,
                        help="""Directory containing RRF files.""")
    args = parser.parse_args()
    return args


def main(rrf_dir):
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

    print("==================")
    print(" SDSI ATOM COUNTS ")
    print("==================")
    counts = sdsi.groupby("CUI")["AUI"].agg("count")
    counts = counts.sort_values(ascending=True)
    skewness = skew(counts)
    kurt = kurtosis(counts)
    example_low = list(counts.index[:3])
    example_high = list(counts.index[-3:])
    print(f"Min: {min(counts)} ({example_low})")
    print(f"Max: {max(counts)} ({example_high})")
    print(f"Mean {counts.mean():.2f} +/- {counts.std():.2f}")
    print(f"Skew: {skewness:.2f}")
    print(f"Kurtosis: {kurt:.2f}")
    print("---------")
    umls_sdsi = sdsi[sdsi["SAB"] == "UMLS"]
    umls_counts = umls_sdsi.groupby("CUI")["SCODE"].apply(set).apply(len)
    umls_counts = umls_counts.sort_values(ascending=True)
    umls_skew = skew(umls_counts)
    umls_kurt = kurtosis(umls_counts)
    ex_umls_low = list(umls_counts.index[:3])
    ex_umls_high = list(umls_counts.index[-3:])
    print(f"Unique UMLS CUIs per SDSI")
    print(f"Min: {min(umls_counts)} ({ex_umls_low})")
    print(f"Max: {max(umls_counts)} ({ex_umls_high})")
    print(f"Mean: {umls_counts.mean():.2f} +/- {umls_counts.std():.2f}")
    print(f"Skew: {umls_skew:.2f}")
    print(f"Kurtosis: {umls_kurt:.2f}")
    n_uniq_cuis = len(set(umls_sdsi["SCODE"]))
    n_sdsi = len(set(umls_sdsi["CUI"]))
    print(f"CUIs / SDSIs: {n_uniq_cuis/n_sdsi}")
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
    main(args.rrf_dir)
