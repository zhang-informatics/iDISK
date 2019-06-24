import json
import argparse
import re

from idlib import Atom, Concept, Attribute, Relationship


def parse_args():
    """
    Set up arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--content_file", type=str,
                        required="True",
                        help="JSONL content file created by ExtractDriver.py")
    parser.add_argument("--idisk_format_output", type=str,
                        required=True,
                        help="iDISK format output file")
    args = parser.parse_args()
    return args


"""
The class for converting raw MSKCC data to iDISK format
"""


class MSKCC_Converter(object):
    """
    Map each extracted info into iDISK format:
    - Atom: self.generate_atom()
    - Concept: self.generate_concept()
    - Attribute: self.generate_attr()
    - Relationship: self.generate_rel()
    """
    def __init__(self, content_file, idisk_format_output):
        """
        MSKCC_Converter constructor

        :param str content_file: full path to raw MSKCC JSONL file
        :param str idisk_format_output: iDISK format JSONL output
        """
        # raw MSKCC data file path
        self.content_file = content_file
        self.idisk_format_output = idisk_format_output

    def remove_useless_for_HDI(self, content):
        """
        Remove content after colon (:), if colon appreas in HDI content
        Remove useless content, like () area, in the contnet
        Remove non-ASCII char in the content
        Strip whitespaces for all content
        Save the cleaned input into list
        Return the list

        :param list/str content: the HDI content
        :return: the removed input
        :rtype: list
        """
        if isinstance(content, list):
            output = [each.split(":")[0] for each in content]
            output = [re.sub(r" ?\([^)]+\)", "", each) for each in output]
            output = [re.sub(r'[^\x00-\x7F]+', " ", each) for each in output]
            output = [each.strip() for each in output]
            return output
        else:
            output = [content.split(":")[0]]
            output = [re.sub(r" ?\([^)]+\)", "", each) for each in output]
            output = [re.sub(r'[^\x00-\x7F]+', " ", each) for each in output]
            output = [each.strip() for each in output]
            return output

    def split_scientific_name(self, sn):
        """
        Split scientific name into list
        Split it by "; ", ", "

        :param str sn: scientific name
        :return: a list of seperated scientific name
        :rtype: list
        """
        # scientific name must be string
        splited_sn = sn.split("; ")
        output = []
        for each in splited_sn:
            output.extend(each.split(", "))
        return output

    def iterate_mskcc_file(self):
        """
        For MSKCC source data ONLY
        Iterate the extracted JSONL file
        For each line, generate iDISK format for each input

        Mapping details:
        MSKCC headers           iDISK schemas           iDISK data types        Relationship (if any)  # noqa
        scientific_name         Scientific Name         Atom                    None  # noqa
        common_names            Synonym                 Atom                    None  # noqa
        clinical_summary        Background              Attribute               None  # noqa
        purported_uses          Diseases                Concept                 effects_on  # noqa
                                                                                inverse_effects_on
        mechanism_of_action     Mechanism of Action     Attribute               None  # noqa
        warnings                Safety                  Attribute               None  # noqa
        adverse_reactions       Signs                   Concept                 has_adverse_reaction  # noqa
                                Symptoms                                        adverse_reaction_of
        herb-drug_interactions  Pharmacological drug    Concept                 interact_with  # noqa
        original herb name      Preferred Name          Concept                 None  # noqa
                                Semantic
                                Dietary Supplement Ingredient (SDSI)
        """
        counter = 0
        with open(self.content_file, "r") as f:
            # use counter as herb id
            for line in f:
                items = json.loads(line)
                hdi = self.remove_useless_for_HDI(items["herb-drug_interactions"])  # noqa
                hdi_atom, counter = self.generate_atom(hdi, counter, "SY")
                print("=====================================")
                print("Currently processing: " + items["herb_name"])
                """
                TODO:
                Current HDI problems:
                1. Zeolite has "general: ....." content,
                   currently pre-processing will only keep "general"
                2. how to properly deal with empty content?
                3. "None reported" content in HDI
                """
                # print("HDI Atoms: ")
                # print(hdi_atom)
                print("Scientific name Atoms: ")
                sn = items["scientific_name"]
                sn_atoms, counter = self.generate_atom(sn, counter,"SN")
                print(sn_atoms)
                print("=====================================")

    def generate_atom(self, content, counter, term_type):
        """
        Given the input, generate an iDISK Atom
        Return the generated iDISK Atom

        :param str content: the extracted content that needs to map to Atom
        :param int counter: counter as Atom's src_id
        :param str term_type: Atom term type
        :return: the generated iDISK Atom
        :rtype: list
        """
        # for HDI content, it's type must be list
        # content is either list or string, string could be empty, like ""
        atoms = []
        if isinstance(content, list):
            for each in content:
                atom = Atom(each, src="MSKCC", src_id=str(counter),
                            term_type=term_type, is_preferred=True)
                counter += 1
                atoms.append(atom)
        else:
            # check if the content is empty
            if len(content) != 0:
                atom = Atom(content, src="MSKCC", src_id=str(counter),
                            term_type=term_type, is_preferred=True)
                counter += 1
                atoms.append(atom)
        return (atoms, counter)

    def test(self):
        """
        a test function
        """
        self.iterate_mskcc_file()


if __name__ == "__main__":
    args = parse_args()
    x = MSKCC_Converter(args.content_file, args.idisk_format_output)
    x.test()
