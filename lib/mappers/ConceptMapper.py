import os
import json
import argparse
from idlib import Atom, Concept, Attribute, Relationship


class ConceptMapper(object):
    """
    Map each extracted info into iDISK format:
    - Atom: self.generate_atom()
    - Concept: self.generate_concept()
    - Attribute: self.generate_attr()
    - Relationship: self.generate_rel()
    """

    def __init__(self):
        pass

    def parse_arg(self):
        """
        Set up arguments
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("--file_location", type=str,
                            required=True,
                            help="the parent path of for file_con")
        parser.add_argument("--file_con", type=str,
                            required=True,
                            help="JSONL file to store herb and its content")

    def remove(self, content):
        """
        Take all content before colon (:), if colon appears in the content
        Save the cleaned input into list
        Return the cleaned input

        :param list/str content: the input that needs to be concated
        :return: the concated input
        :rtype: list
        """
        if isinstance(list, content):
            output = []

    def iterate_mskcc_file(self, path, read_file):
        """
        For MSKCC source data ONLY
        Iterate the extracted JSONL file
        For each line, generate iDISK format for each input

        Mapping details:
        MSKCC headers       iDISK schemas       iDISK data types        Relationship (if any)  # noqa
        scientific_name     Scientific Name     Atom        None  # noqa
        common_names        Synonym     Atom        None  # noqa
        clinical_summary        Background      Attribute       None  # noqa
        purported_uses      Diseases        Concept     effects_on/"inverse_effects_on  # noqa
        mechanism_of_action     Mechanism of Action     Attribute       None  # noqa
        warnings        Safety      Attribute       None  # noqa
        adverse_reactions       Signs/Symptoms      Concept     has_adverse_reaction/adverse_reaction_of  # noqa
        herb-drug_interactions      Pharmacological drug        Concept     interact_with  # noqa
        original herb name      Preferred Name/Semantic Dietary Supplement Ingredient (SDSI)        Concept     None  # noqa

        :param str path: the parent path of the extracted JSONL file
        :param str read_file: the file name of the the extracted JSONL file
        """
        with open(os.path.join(path, read_file), "r") as f:
            for line in f:
                # load all extracted info
                items = json.loads(line)

    def generate_atom(self, info, line_number):
        """
        Given the input, generate an iDISK Atom
        Return the generated iDISK Atom

        :param str info: the extracted content that needs to map to Atom
        :param int line_number: the line number that the content fits in
        :return: the generated iDISK Atom
        :rtype: idlib.Atom
        """
