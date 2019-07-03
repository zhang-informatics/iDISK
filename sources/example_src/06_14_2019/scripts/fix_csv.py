import sys
import codecs
import re
import argparse

"""
Fixes various issues with CSV formatting in
NHP Medicinal Ingredients data: incorrect newlines
and extra commas.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", type=str, required=True,
                        help="CSV file to fix.")
    parser.add_argument("--numfields", type=int, required=True,
                        help="Number of fields")
    parser.add_argument("--encoding", type=str, default='utf-8',
                        help="File encoding")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    data = codecs.open(args.infile, 'r', args.encoding).read()
    line_buf = ""
    n_fields = 1
    in_quote = False
    ignore = False
    datasize = len(data)
    for (i, char) in enumerate(data):
        # Check the newline is in the correct place.
        if char == '\n':
            if in_quote is True:
                msg = "Incorrect newline at character position"
                sys.stderr.write("{} {}: {}\n".format(msg, i, line_buf))
                continue
            elif n_fields == args.numfields:
                if i+1 == datasize or re.search(r'[0-9]+', data[i+1:i+7]):
                    print(line_buf, end='')
                    n_fields = 1
                    line_buf = ""
                    ignore = False
                else:
                    msg = "Incorrect newline at character position"
                    sys.stderr.write("{} {}: {}\n".format(msg, i, line_buf))
                    continue
            else:
                msg = "Incorrect newline at character position"
                sys.stderr.write("{} {}: {}\n".format(msg, i, line_buf))
                continue
        # Make sure quotes are correct.
        elif char == '"':
            if in_quote is False:
                in_quote = True
            else:
                in_quote = False
        elif char == ',':
            if in_quote:
                pass
            elif n_fields == args.numfields:
                msg = "Trailing comma at character position"
                sys.stderr.write("{} {}: {}\n".format(msg, i, line_buf))
                ignore = True
                continue
            else:
                n_fields += 1
        if not ignore:
            line_buf += char

    if line_buf:
        print(line_buf, end='')


if __name__ == '__main__':
    main()
