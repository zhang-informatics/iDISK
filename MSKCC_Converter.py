import json
import argparse

from idlib import Atom, Concept, Attribute, Relationship


def parse_args():
    """
    Set up arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--content_file", type=str,
                        required=True,
                        help="JSONL file that stores herb and contents")
    parser.add_argument("--idisk_output", type=str,
                        required=True,
                        help="JSONL file to store iDISK format")


class MSKCC_Converter(object):
    """
    Map each extracted info into iDISK format:
    - Atom: self.generate_atom()
    - Concept: self.generate_concept()
    - Attribute: self.generate_attr()
    - Relationship: self.generate_rel()
    """

    def __init__(self, content_file):
        """
        MSKCC_Converter constructor

        :param str content_file: full path to extracted MSKCC JSONL file
        """
        self.content_file = content_file

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
            output = [each.split(":")[0] for each in content]
            return output
        else:
            return [content.split(":")[0]]

    def iterate_mskcc_file(self, content_file, source):
        """
        For MSKCC source data ONLY
        Iterate the extracted JSONL file
        For each line, generate iDISK format for each input

        Mapping details:
        MSKCC headers       iDISK schemas       iDISK data types        Relationship (if any)  # noqa
        scientific_name     Scientific Name     Atom        None  # noqa
        common_names        Synonym     Atom        None  # noqa
        clinical_summary        Background      Attribute       None  # noqa
        purported_uses      Diseases        Concept     effects_on/inverse_effects_on  # noqa
        mechanism_of_action     Mechanism of Action     Attribute       None  # noqa
        warnings        Safety      Attribute       None  # noqa
        adverse_reactions       Signs/Symptoms      Concept     has_adverse_reaction/adverse_reaction_of  # noqa
        herb-drug_interactions      Pharmacological drug        Concept     interact_with  # noqa
        original herb name      Preferred Name/Semantic Dietary Supplement Ingredient (SDSI)        Concept     None  # noqa

        :param str content_file: the file name of the the extracted JSONL file
        :param str source: data source
        """
        with open(content_file, "r") as f:
            for line in f:
                # counter as Atom's src_id
                # TODO: discuss with Jake about better src_id choice
                counter = 0
                # load all extracted info
                items = json.loads(line)

    def generate_atom(self, info, counter, source, term_type):
        """
        Given the input, generate an iDISK Atom
        Return the generated iDISK

        :param str info: the extracted content that needs to map to Atom
        :param int counter: counter as Atom's src_id
        :param str source: data source
        :param str term_type: Atom term type
        :return: the generated iDISK Atom
        :rtype: idlib.Atom
        """
        cleaned_info = self.remove(info)
        atoms = []
        # add each term in the input as iDISK Atom
        for each in cleaned_info:
            atom = Atom(each, src=source, src_id=source+str(counter),
                        term_type=term_type, is_preferred=True)
            atoms.append(atom)
            # increase counter
            counter += 1
        return atoms
