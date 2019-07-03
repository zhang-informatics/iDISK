import argparse
import json
import re
import string
import pandas as pd

from idlib import Atom, Concept, Relationship

"""
Formats product and ingredient information from NHP
into the iDISK JSON lines format.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ingredients_csv", type=str, required=True,
                        help="""Input CSV file containing ingredient
                                information. E.g.
                                NHP_MEDICINAL_INGREDIENTS_fixed_ids.csv""")
    parser.add_argument("--products_csv", type=str, required=True,
                        help="""Input CSV file containing product information,
                                e.g. NHP_PRODUCTS.csv""")
    parser.add_argument("--outjsonl", type=str, required=True,
                        help="Where to save the output JSON lines file.")
    args = parser.parse_args()
    return args


def extract_concepts(ingredients_csv, products_csv, outjsonl):
    """
    The driver function.

    :param str ingredients_csv: Path to ingredients CSV file.
    :param str products_csv: Path to ingredients CSV file.
    :param str outjsonl: Where to save the resulting ingredients.
    """
    print("Creating ingredient concepts")
    ingredients_data = pd.read_csv(ingredients_csv, dtype=str)
    ingredient_concepts = create_ingredient_concepts(ingredients_data)
    print("  merging ingredient concepts")
    ingredient_concepts = merge_duplicate_concepts(ingredient_concepts)

    print("Creating product concepts")
    products_data = pd.read_csv(products_csv, dtype=str)
    product_concepts = create_product_concepts(products_data)
    print("  merging product concepts")
    product_concepts = merge_duplicate_concepts(product_concepts)

    print("Connecting ingredients to products")
    all_concepts = connect_ingredients_to_products(ingredient_concepts,
                                                   product_concepts)
    with open(outjsonl, 'w') as outF:
        for concept in all_concepts:
            json.dump(concept.to_dict(), outF)
            outF.write('\n')


def merge_duplicate_concepts(concepts):
    """
    NHP has many duplicate ingredients in the raw data. During
    data preprocessing each unique ingredient string is assigned a unique
    ID, so duplicate ingredient entries will have the same ID. This
    function merges those entries into a single concept.

    :param list concepts: List of Concept instances
    """

    def _merge(concept1, concept2):
        """
        Merges the atoms of concept2 into concept1, removing duplicates.
        This merge is performed in place.
        Luckily NHP concepts don't have attributes (yet),
        so we don't have to merge those.
        """
        for atom in concept2.get_atoms():
            if atom not in concept1.get_atoms():
                concept1.atoms.append(atom)
        for rel in concept2.get_relationships():
            if rel not in concept1.get_relationships():
                concept1.relationships.append(rel)

    seen = {}  # {src_id: Concept}
    for (i, concept) in enumerate(concepts):
        print(f"{i}/{len(concepts)}\r", end='')
        src_id = concept.preferred_atom.src_id
        if src_id not in seen:
            seen[src_id] = concept
        else:
            _merge(seen[src_id], concept)  # Changes seen[src_id] in place
    return seen.values()


def create_ingredient_concepts(dataframe):
    """
    Given a Pandas dataframe of ingredient data, create a concept
    for each row.

    :param pandas.DataFrame dataframe: Dataframe containing ingredient data.
    :returns: Generator over concepts created from the dataframe.
    """
    Concept.set_ui_prefix("NHPID")

    concepts = []

    dataframe = dataframe[["ingredient_id", "product_id",
                           "proper_name", "proper_name_f",
                           "common_name", "common_name_f"]].copy()
    dataframe.dropna(subset=["proper_name"], axis=0, inplace=True)
    dataframe.drop_duplicates(inplace=True)
    dataframe.fillna("", inplace=True)
    synonym_cols = ["proper_name_f", "common_name", "common_name_f"]

    seen = set()
    for (i, row) in enumerate(dataframe.itertuples()):
        print(f"{i}/{dataframe.shape[0]}\r", end='')
        row = row._asdict()
        pref_term = row["proper_name"]
        src_id = row["ingredient_id"].replace(".0", '')
        if invalid_ingredient_name(pref_term):
            print(f"Removing invalid ingredient with name '{pref_term}'")
            continue

        pref_atom = Atom(term=pref_term, src="NHPID", src_id=src_id,
                         term_type="SN", is_preferred=True)
        atoms = [pref_atom]
        # Extract the synonyms, removing any empty strings
        # or duplicate string-termtype pairs.
        seen.add((pref_term, "SN"))
        for column in synonym_cols:
            term = row[column]
            tty = "SN" if column == "proper_name_f" else "SY"
            if not term or (term, tty) in seen:
                continue
            seen.add((term, tty))
            atom = Atom(term=term, src="NHPID", src_id=src_id,
                        term_type=tty, is_preferred=False)
            atoms.append(atom)

        concept = Concept(concept_type="SDSI", atoms=atoms)

        product_id = row["product_id"].replace(".0", '')
        rel = Relationship(subject=concept,
                           rel_name="ingredient_of",
                           obj=product_id,
                           src="NHPID")
        concept.relationships.append(rel)

        concepts.append(concept)
    return concepts


def invalid_ingredient_name(name):
    """
    A ingredient name is invalid if it is empty,
    less than two characters, is only numeric, characters,
    or is only punctuation.

    :param str name: The ingredient name to check.
    :rtype bool:
    """
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


def create_product_concepts(dataframe):
    """
    Given a Pandas dataframe of product data, create a concept
    for each row.

    :param pandas.DataFrame dataframe: Dataframe containing product data.
    :returns: Generator over concepts created from the dataframe.
    """
    Concept.set_ui_prefix("NHPID")

    concepts = []
    dataframe = dataframe[["product_id", "product_name"]].copy()
    for (i, row) in enumerate(dataframe.itertuples()):
        print(f"{i}/{dataframe.shape[0]}\r", end='')
        row = row._asdict()
        src_id = row["product_id"].replace(".0", '')
        atom = Atom(term=str(row["product_name"]), src="NHPID",
                    src_id=src_id, term_type="SY",
                    is_preferred=True)
        concept = Concept(concept_type="DSP", atoms=[atom])
        concepts.append(concept)
    return concepts


def connect_ingredients_to_products(ingredient_concepts, product_concepts):
    """
    Look for all the "ingredient_of" relationships in each ingredient concept,
    update the object of these relationships to be a product concept from a
    product ID, and create the inverse "has_ingredient" relationship.

    :param list ingredient_concepts: List of ingredient Concept instances.
    :param list product_concepts: List of product Concept instances.
    :returns: List of all Concept instances with updated relationships.
    :rtype: list
    """
    # {product_id: product_concept}
    id2product = dict([(c.preferred_atom.src_id, c)
                       for c in product_concepts])
    for (i, ing) in enumerate(ingredient_concepts):
        print(f"{i}/{len(ingredient_concepts)}\r", end='')
        for rel in ing.get_relationships("ingredient_of"):
            product_id = rel.object
            try:
                product = id2product[product_id]
            except KeyError:
                print(f"Missing product {product_id} for ingredient {ing}.")
                continue
            rel.object = product
            has_ing_rel = Relationship(subject=product,
                                       rel_name="has_ingredient",
                                       obj=ing,
                                       src="NHPID")
            product.relationships.append(has_ing_rel)

    return list(ingredient_concepts) + list(product_concepts)


if __name__ == "__main__":
    args = parse_args()
    extract_concepts(args.ingredients_csv, args.products_csv, args.outjsonl)
