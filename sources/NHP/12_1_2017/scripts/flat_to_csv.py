import os
import argparse
import pandas as pd

"""
Converts a given flat format files as downloaded from
the NHP website into CSV files.
Downloaded files are stored in original_files/, which contains
headers/, which holds column names for each file as extracted
from the NHP README (NHP_README.txt).
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", type=str, required=True,
                        help="Original NHP file to convert to CSV.")
    parser.add_argument("--headerfile", type=str, required=True,
                        help="""File containing column headers for infile,
                                one per line.""")
    parser.add_argument("--outdir", type=str, required=True,
                        help="Directory in which to save the CSV.")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    basename = os.path.basename(args.infile)
    outfile = "{}.csv".format(os.path.splitext(basename)[0])
    outfile = os.path.join(args.outdir, outfile)

    header = [line.strip() for line in open(args.headerfile, 'r').readlines()]
    data = pd.read_csv(args.infile, sep='|', names=header, encoding="latin1")
    data.to_csv(outfile, header=True, index=False, encoding='utf-8', na_rep='')


if __name__ == '__main__':
    main()
