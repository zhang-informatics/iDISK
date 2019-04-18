import argparse
import json

'''
Converts an iDISK JSON lines file containing ingredients matched
between two data sources into the Prodigy JSON lines format
for manual annotation.
'''


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingredients_file", type=str, required=True,
                        help="""iDISK JSON lines file containing
                                matched ingredients.""")
    parser.add_argument("--outfile", type=str, required=True,
                        help="Where to save the output file.")
    args = parser.parse_args()
    return args


def main(ingredients_file, outfile):
    with open(ingredients_file, 'r') as inF:
        with open(outfile, 'w') as outF:
            for ingredient in inF:
                ingredient_json = json.loads(ingredient)
                prodigy_json = to_prodigy(ingredient_json)
                json.dump(prodigy_json, outF)
                outF.write('\n')


def to_prodigy(ingredient):
    '''
    Given the iDISK JSON representation of an ingredient,
    returns the Prodigy JSON for manual review.
    '''
    pref_name1, src1 = ingredient["preferred_term"], ingredient["src"]
    try:
        pref_name2, src2 = [(term["term"], term["src"])
                            for term in ingredient["synonyms"]
                            if term["src"] != src1 and
                            term["is_preferred"] is True][0]
    except IndexError:
        raise IndexError(f"No alternate source found for ingredient {ingredient['preferred_term']}")  # noqa

    # Find the synonyms that the two ingredients were matched on.
    synonyms = [syn["term"] for syn in ingredient["synonyms"]]
    synonyms.append(ingredient["preferred_term"])
    # Lowercase all to make sure they match.
    synonyms = [syn.lower() for syn in synonyms]
    matched_synonyms = get_duplicates(synonyms)

    outjson = {"ing1": {"term": pref_name1, "src": src1},
               "ing2": {"term": pref_name2, "src": src2},
               "matched_synonyms": sorted(matched_synonyms)}
    return outjson


def get_duplicates(seq):
    seen = set()
    seen_add = seen.add
    duplicates = set(x for x in seq if x in seen or seen_add(x))
    return list(duplicates)


if __name__ == "__main__":
    args = parse_args()
    main(args.ingredients_file, args.outfile)
