import argparse
import requests
import json


"""
Makes a GET request for each supplied DSLD product id.
Write the resulting JSON to a JSON lines file.
"""

class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--product_ids", type=str, required=True,
                        help="Newline delimited file of DSLD product IDs.")
    parser.add_argument("--outfile", type=str, required=True,
                        help="Where to save the JSON output.")
    args = parser.parse_args()
    return args


def get_labels(product_ids, outfile):

    def _url(path):
        return "https://dsld.nlm.nih.gov/dsld/api/label/" + path

    last_written = None
    for (i, pid) in enumerate(product_ids):
        try: 
            print(f"{i+1}/{len(product_ids)}\r", end="")
            resp = requests.get(_url(pid))
            if resp.status_code != 200:
                raise APIError(resp.status_code)
            else:
                with open(outfile, 'a') as outF:
                    json.dump(resp.json(), outF)
                    outF.write('\n')
                last_written = pid
        except KeyboardInterrupt:
            print(f"Last written product: {last_written}")
            return


if __name__ == "__main__":
    args = parse_args()
    product_ids = [l.strip() for l in open(args.product_ids)]
    get_labels(product_ids, args.outfile)
