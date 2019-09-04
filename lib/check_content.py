import os
import re
import argparse
import json
import logging

from idlib import Schema


"""
This script takes in one or more iDISK formatted JSON lines files
and lints them against the current schema in order to find any
discrepancies.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--concept_files", nargs='*', default=[],
                        help="""Paths to all JSON lines concepts
                                files to check.""")
    parser.add_argument("--schema_uri", type=str, default="localhost",
                        help="""The URI of the Neo4j graph
                                containing the schema.""")
    parser.add_argument("--schema_user", type=str, default="neo4j",
                        help="""The user of the Neo4j graph
                                containing the schema.""")
    parser.add_argument("--schema_password", type=str, default="password",
                        help="""The password of the Neo4j graph
                                containing the schema.""")
    args = parser.parse_args()
    if args.concept_files == []:
        parser.error("At least one concept file is required.")
    return args


def log_to_file(warnings, infile, outfile):
    logger = logging.getLogger(os.path.basename(infile))
    handler = logging.FileHandler(outfile)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    for warning in warnings:
        logger.warning(warning)

    logger.removeHandler(handler)


def check_attribute(attribute, node):
    warnings = set()
    name = attribute["atr_name"]
    value = attribute["atr_value"]
    if attribute["atr_name"] not in node.keys():
        warnings.add(f"Unknown attribute name '{name}'.")
    if '\n' in value or '\t' in value or '\r' in value:
        msg = f"Bad whitespace (newline or tab) in '{value}'."
        warnings.add(msg)
    return warnings


def main(infiles, schema):
    for inF in infiles:
        print(f"Checking '{inF}'.")
        warnings = set()

        # Check for improper JSON
        data = []
        for (i, line) in enumerate(open(inF, 'r')):
            i += 1
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                warnings.add(f"Bad JSON at line {i}. Skipping...")

        for concept in data:
            # Check the concept type
            label = concept["concept_type"]
            node = schema.get_node_from_label(label)
            if node is None:
                warnings.add(f"Label '{label}' not in schema.")

            for syn in concept["synonyms"]:
                term = syn["term"]
                if '\n' in term or '\t' in term or '\r' in term:
                    msg = f"Bad whitespace (newline or tab) in '{term}'."
                    warnings.add(msg)

            # Check the UI format
            if not re.match(r'[a-zA-Z]+[0-9]{7}', concept["ui"]):
                warnings.add(f"Improperly formatted UI: '{concept['ui']}'")

            # Check the attributes
            if node is not None:
                for atr in concept["attributes"]:
                    warnings.update(check_attribute(atr, node))

                for rel in concept["relationships"]:
                    rel_name = rel["rel_name"]
                    edge = schema.get_relationship_from_name(rel_name)
                    if edge is None:
                        msg = f"Relationship '{rel_name}' not in schema."
                        warnings.add(msg)
                        continue
                    for rel_atr in rel["attributes"]:
                        warnings.update(check_attribute(rel_atr, edge))

        print(f"{len(warnings)} issues found.")
        if len(warnings) > 0:
            outfile = f"{inF}.error"
            print(f"Saving issues to '{outfile}'.")
            log_to_file(warnings, inF, outfile)


if __name__ == "__main__":
    args = parse_args()
    print("Connecting to schema graph...", end='')
    schema = Schema(args.schema_uri, args.schema_user, args.schema_password)
    print("Connected")
    main(args.concept_files, schema)
