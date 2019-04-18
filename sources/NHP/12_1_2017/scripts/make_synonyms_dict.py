import argparse
import json
import pandas as pd

"""
Extracts synonyms from NHPID data using the proper_name column as the
preferred term, the common_name and common_name_f columns as the common names
and the proper_name and proper_name_f columns as the scientific names.
{PT: str,
 ID: int,
 PT_tty: str,
 CN: [str],
 SN: [str]}
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("incsv", type=str,
                        help="NHP_MEDICINAL_INGREDIENTS_fixed_ids.csv")
    parser.add_argument("outjson", type=str,
                        help="Where to save the synonyms.")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    nhpid_data = pd.read_csv(args.incsv)
    # PN: Preferred Term, CN: Common Name, SN: Scientific Name
    outcols = ["PT", "ID", "PT_tty", "CN", "SN"]
    outdata = pd.DataFrame(columns=outcols)

    PT_column = "proper_name"
    PT_tty = "SN"  # Term type of preferred term.
    CN_columns = ["common_name", "common_name_f"]
    SN_columns = ["proper_name", "proper_name_f"]

    # Extract the names
    nhpid_data = nhpid_data[CN_columns + SN_columns + ["ingredient_id"]]
    nhpid_data = nhpid_data.dropna(subset=[PT_column], axis=0)
    nhpid_data.drop_duplicates(inplace=True)

    outdata.PT = nhpid_data[PT_column]
    outdata.ID = nhpid_data["ingredient_id"]
    outdata.PT_tty = PT_tty
    outdata.CN = [filter(lambda x: not pd.isnull(x), a)
                  for a in nhpid_data[CN_columns].values]
    outdata.SN = [filter(lambda x: not pd.isnull(x), a)
                  for a in nhpid_data[SN_columns].values]

    # Remove any duplicates within the common and scientific names.
    outdata.CN = [list(set(a)) for a in outdata.CN]
    outdata.SN = [list(set(a)) for a in outdata.SN]
    print(outdata.shape)

    outjson = outdata.to_json(orient="records", force_ascii=False)
    outjson = json.loads(outjson)
    with open(args.outjson, 'w', encoding="utf-8") as outF:
        json.dump(outjson, outF, indent=4,
                  sort_keys=False, ensure_ascii=False)


if __name__ == "__main__":
    main()
