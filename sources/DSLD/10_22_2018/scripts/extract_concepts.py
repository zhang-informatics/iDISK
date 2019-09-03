import logging
import argparse
import json
import re
import pandas as pd
from collections import OrderedDict
from nltk.corpus import stopwords

from idlib import Atom, Concept, Attribute, Relationship

"""
Obtains all the synonyms of the DSLD manual download
and saves them as a JSON lines file.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingredients_file", type=str, required=True,
                        help="""CSV file containing DSLD ingredients
                                and synonyms.""")
    parser.add_argument("--products_file", type=str, required=True,
                        help="JSON lines file containing DSLD products.")
    parser.add_argument("--outfile", type=str, required=True,
                        help="Where to save the concepts as JSON lines.")
    parser.add_argument("--filter_words", type=str, default=None,
                        help="""Path to file containing words to filter,
                                one per line. Note that this script filters
                                stopwords from nltk.corpus.stopwords('english')
                                by default.""")
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    # ======================================
    # Process the ingredients data
    # ======================================
    ingredients_data = read_ingredients_data(args.ingredients_file)

    # Split the list of synonyms for each ingredient group into multiple rows.
    # E.g. 1,Ginseng,"Ginseng;ginsang;ginseng panax" -->
    # 1,Ginseng,"ginseng"
    # 1,Ginseng,"ginsang"
    # 1,Ginseng,"ginseng panax"
    # Column names are now "group_id", "group_name", "synonym".
    ingredients_split = split_synonyms(ingredients_data)

    # Apply a series of regular expressions to normalize the synonyms.
    filter_words = stopwords.words("english")
    if args.filter_words is not None:
        filter_words = filter_words + \
                       [w.strip() for w in open(args.filter_words)]
    regexes = get_regexes(filter_words)
    # Apply the apply_regexes function to every synonym.
    ingredients_split["synonym"] = ingredients_split["synonym"].apply(
                                    apply_regexes, args=(regexes,))
    ingredients_split.drop_duplicates(inplace=True)
    ingredients_split["synonym"].replace('', pd.np.nan, inplace=True)
    ingredients_split.dropna(subset=["synonym"], inplace=True)

    # Expand out "hidden" synonyms, such as in Acai (Euterpe oleracea).
    ingredients_split = expand_ingredients(ingredients_split)
    ingredients_split.drop_duplicates(inplace=True)

    # Merge multiple synonyms for the same group name into a single row.
    ingredients_split = merge_groups(ingredients_split)

    # Create the ingredient concepts
    ingredient_concepts = convert_ingredients_to_concepts(ingredients_split)

    # ======================================
    # Process the products data
    # ======================================
    products_data = read_products_data(args.products_file)
    product_concepts = convert_products_to_concepts(products_data)

    all_concepts = connect_products_to_ingredients(product_concepts,
                                                   ingredient_concepts)

    with open(args.outfile, 'w') as outF:
        for concept in all_concepts:
            json.dump(concept.to_dict(), outF)
            outF.write("\n")


def read_ingredients_data(infile):
    """
    Read the ingredients data from the CSV file at infile
    into a pandas DataFrame.

    :param str infile: The CSV file to read.
    :returns: ingredients data
    :rtype: pandas.DataFrame
    """
    ingredients_data = pd.read_csv(infile,
                                   dtype={"Ingredient - Group ID": int})
    ingredients_data = ingredients_data[["Ingredient - Group ID",
                                         "Ingredient - Group Name",
                                         "Synonyms/Sources"]]
    ingredients_data.drop_duplicates(inplace=True)
    ingredients_data.columns = ["group_id", "group_name", "synonyms"]
    return ingredients_data


def read_products_data(infile):
    """
    Read the products data from the JSON lines file at infile
    and return the result as a list of dicts.

    :param str infile: JSON lines file to read.
    :returns: products data
    :rtype: list
    """
    products_data = [json.loads(line.strip()) for line in open(infile, 'r')]
    return products_data


def connect_products_to_ingredients(product_concepts, ingredient_concepts):
    """
    Given a set of ingredient and product Concept instances, update the object
    of the has_ingredient Relationships to be the ingredient instances.

    :param list product_concepts: List of Concepts of type DSP.
    :param list ingredient_concepts: List of Concepts of type SDSI.
    :returns: List of both product and ingredient concepts, with
              ingredient_of Relationships.
    :rtype: list
    """
    id2ingredient = dict([(c.preferred_atom.src_id, c)
                          for c in ingredient_concepts])
    num_missing_ingredients = 0
    for (i, product) in enumerate(product_concepts):
        print(f"{i+1}/{len(product_concepts)}\r", end='')
        for rel in product.get_relationships("has_ingredient"):
            ingredient_id = rel.object
            try:
                ingredient_concept = id2ingredient[ingredient_id]
                rel.object = ingredient_concept
            except KeyError:
                logging.warning(f"Unable to find ingredient {ingredient_id} of product {product}.")  # noqa
                num_missing_ingredients += 1
                product.rm_elements(rel)
                continue

    logging.warning(f"Couldn't find {num_missing_ingredients} ingredients.")
    return ingredient_concepts + product_concepts


def convert_products_to_concepts(json_data):
    Concept.set_ui_prefix("DSLD")
    concepts = []
    for line in json_data:
        atom = Atom(term=line["Product_Name"],
                    src="DSLD", src_id=line["DSLD_ID"],
                    term_type="SY", is_preferred=True)
        concept = Concept(concept_type="DSP", atoms=[atom])

        # LanguaL Product Type attribute
        if line["LanguaL_Product_Type"]:
            atr = Attribute(subject=concept,
                            atr_name="langual_type",
                            atr_value=line["LanguaL_Product_Type"],
                            src="DSLD")
            concept.add_elements(atr)

        for ing in line["ingredients"]:
            ing_id = ing["Ingredient_Group_GRP_ID"]
            has_ing_rel = Relationship(subject=concept,
                                       rel_name="has_ingredient",
                                       object=ing_id,
                                       src="DSLD")
            concept.add_elements(has_ing_rel)

        concepts.append(concept)
    return concepts


def split_synonyms(dataframe):
    """
    Acai, acai (euterpe oleracea) juice;acai
    becomes
    Acai, acai (euterpe oleracea) juice
    Acai, acai
    """
    new_df = []
    for row in dataframe.itertuples():
        syns = [s.strip() for s in row.synonyms.replace('"', '').split(';')]
        for syn in syns:
            line = OrderedDict({"group_name": row.group_name,
                                "group_id": str(row.group_id),
                                "synonym": syn})
            new_df.append(line)
    return pd.DataFrame(new_df)


def get_regexes(filter_words):
    """
    param filter_words list: Words to remove.
    """

    def rm_extra_space(func):
        def wrapper(*args):
            return ' '.join(func(*args).split())
        return wrapper

    regexes = []

    # Remove all text after 2 or more spaces
    space_split_re = re.compile(r"[ \t]{2,}")
    @rm_extra_space  # noqa
    def split_spaces(string): return space_split_re.split(string)[0]
    regexes.append(split_spaces)

    # Remove dosages
    units = ["g", "mg", "mcg", "iu", r"i\.u\.", "%"]
    units_re = r"(" + r"|".join(units) + r")"
    rm_dose_re = re.compile(fr"\b[0-9,.]+ ?{units_re}(?:\s|$)",
                            re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_doses(string): return rm_dose_re.sub("", string)
    regexes.append(rm_doses)

    # Remove ratios
    rm_ratio_re = re.compile(r"\b[0-9]+:[0-9]+\b", re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_ratios(string): return rm_ratio_re.sub("", string)
    regexes.append(rm_ratios)

    # Remove rights reserved (r), trademark (tm), and copyright (c)
    rm_rights_re = re.compile(r"\((r|tm|c)\)", re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_rights(string): return rm_rights_re.sub("", string)
    regexes.append(rm_rights)

    # Remove balanced single quotes. E.g. "'I' saw it" -> "I saw it"
    rm_quoted_re = re.compile(r"(\s|^)'(.*?)'(\s|$)", re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_quotes(string): return rm_quoted_re.sub(r"\1\2\3", string)
    regexes.append(rm_quotes)

    # Remove curly braces
    rm_braces_re = re.compile(r"[\{\}]", re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_braces(string): return rm_braces_re.sub("", string)
    regexes.append(rm_braces)

    # Remove stop words
    pattern = r"\b(" + r"|".join(stopwords.words("english")) + r")\b"
    rm_stop_words_re = re.compile(pattern, re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_stop_words(string): return rm_stop_words_re.sub("", string)
    regexes.append(rm_stop_words)

    # Remove filter words if they occur within
    # parentheses, braces, or brackets.
    filter_words = [fw.strip().lower() for fw in filter_words]
    pattern = r"[\(\[\{](" + r"|".join(filter_words) + r")[\)\]\}]"
    rm_filter_words_re = re.compile(pattern, re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_filter_words(string): return rm_filter_words_re.sub("", string)
    regexes.append(rm_filter_words)

    # Remove other unwanted punctuation
    rm_punct_re = re.compile(r":", re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_punct(string): return rm_punct_re.sub("", string)
    regexes.append(rm_punct)

    # Remove numbers within parentheses
    rm_num_re = re.compile(r"\([0-9]+\)", re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_num(string): return rm_num_re.sub("", string)
    regexes.append(rm_num)

    # Remove leftover empty parentheses and brackets
    rm_empty_parens_re = re.compile(r"[\(\[][\s,\.]*[\)\]]", re.IGNORECASE)
    @rm_extra_space  # noqa
    def rm_empty_parens(string): return rm_empty_parens_re.sub("", string)
    regexes.append(rm_empty_parens)

    return regexes


def apply_regexes(string, regexes):
    for regex in regexes:
        string = regex(string)
    return string


def expand_ingredients(dataframe):
    """
    1, Acai, acai (euterpe oleracea)  juice
    becomes
    Acai, acai juice
    Acai, euterpe oleracea
    """
    new_rows = []
    for (line, row) in dataframe.iterrows():
        syn = row["synonym"]
        # Remove all words in parentheses from the original line
        # and create new entries for them with the same group id
        # and group name.
        new_syns = re.findall(r'\(.*?\)', syn)
        syn = re.sub(r"\(.*\)", '', syn)
        syn = ' '.join(syn.strip().split())
        new_rows.append(OrderedDict({"group_name": row.group_name,
                                     "group_id": row.group_id,
                                     "synonym": syn}))
        if new_syns != []:
            for ns in new_syns:
                ns = re.sub(r'[\(\)]', '', ns)
                new_rows.append({"group_name": row.group_name,
                                 "group_id": row.group_id,
                                 "synonym": ns})
    new_df = pd.DataFrame(new_rows)
    new_df = new_df.drop_duplicates()
    return new_df


def merge_groups(dataframe):
    """
    Acai, acai juice
    Acai, euterpe oleracea
    becomes
    Acai, [acai juice, euterpe oleracea]
    """
    grouped = dataframe.groupby(["group_name", "group_id"])
    dataframe = grouped["synonym"].apply(list).reset_index()
    dataframe.columns = ["group_name", "group_id", "synonyms"]
    return dataframe


def convert_ingredients_to_concepts(dataframe):
    """
    Each row in dataframe corresponds to an ingredient concept.
    Create a Concept instance for each row.

    :param pd.Dataframe dataframe: Table containing ingredients data.
    :returns: Generator over SDSI concepts.
    :rtype: generator
    """
    dont_include = ["header", "fat calories", "polyunsaturated fat"]

    Concept.set_ui_prefix("DSLD")
    tty = "SY"  # All DSLD terms have term type SY
    # Create a Concept instance for each row.
    concepts = []
    for row in dataframe.itertuples():
        pref_term = row.group_name
        if pref_term.lower() in dont_include:
            continue
        src_id = str(row.group_id)
        pref_atom = Atom(term=pref_term, src="DSLD", src_id=src_id,
                         term_type=tty, is_preferred=True)
        # The Atoms for this concept are its preferred term plus all synonyms.
        atoms = [pref_atom]
        seen = set([pref_term.lower()])
        for syn in row.synonyms:
            if not syn:
                continue
            if syn.lower() in seen:
                continue
            atom = Atom(term=syn, src="DSLD", src_id=src_id,
                        term_type=tty, is_preferred=False)
            atoms.append(atom)
            seen.add(syn.lower())

        concept = Concept(concept_type="SDSI", atoms=atoms)
        concepts.append(concept)
    return concepts


if __name__ == "__main__":
    main()
