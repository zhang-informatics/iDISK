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
            output = [re.sub(r'[^\x00-\x7F]+', "", each) for each in output]
            output = [each.strip() for each in output]
            return output
        else:
            output = [content.split(":")[0]]
            output = [re.sub(r" ?\([^)]+\)", "", each) for each in output]
            output = [re.sub(r'[^\x00-\x7F]+', "", each) for each in output]
            output = [each.strip() for each in output]
            return output

    def split_names(self, names):
        """
        Split scientific & common name into list
        Split it by "; ", ", "

        :param str/list names: scientific/common name
        :return: a list of seperated scientific/common name
        :rtype: list
        """
        # scientific name must be string
        # common name could be list, or empty string
        # empty string case is ignored under iterate_mskcc_file
        if isinstance(names, str):
            output = re.split(", |; ", names)
            return output
        else:
            output = []
            for each in names:
                splited = re.split(", |; ", each)
                output.extend(splited)
            return output

    def split_content(self, content):
        """
        Split the content, e.g. HDI or ADR, into list
        Split it by "\n", "/"
        Do not split on "mh", "mg" and "mL"

        :param str/list content: the content needs to split
        :return: a list contains the splited content
        :rtype: list
        """
        if isinstance(content, str):
            content = content.split("\n")
        content = list(filter(None, content))
        # if an item has number, then it should not be split by "/"
        final_content = []
        for each in content:
            if any(char.isdigit() for char in each):
                final_content.append(each)
            else:
                output = each.split("/")
                final_content.extend(output)
        final_content = list(set(final_content))
        return final_content

    def is_valid_content(self, content):
        """
        check if HDI content is valid
        e.g. if the content is "general", "none reports",
        ignore it and return False,
        otherwise return True

        :param str content: the content to be checked
        :rtype: bool
        """
        if content.lower() == "general" or \
            content.lower() == "none reports." or \
                content.lower() == "none known." or \
                content == "" or \
                content.lower() == "case reports" or \
                any(char.isdigit() for char in content):
            return False
        else:
            return True

    def write_to_local_file(self, concept):
        """
        Write concept into a local file
        Remove duplicate items

        :param list seen_id: concept ids that have beed processed
        :param Concept concept: the concept to be written in the local file
        """
        with open(self.idisk_format_output, "a") as outf:
            json.dump(concept.to_dict(), outf)
            outf.write("\n")

    def iterate_mskcc_file(self):
        """
        For MSKCC source data ONLY
        Iterate the extracted JSONL file
        For each line, generate iDISK format for each input

        Mapping details:
        MSKCC headers           iDISK schemas           iDISK data types        Relationship (if any)  # noqa
        scientific_name         Scientific Name         Atom                    None  # noqa
        common_name             Synonym                 Atom                    None  # noqa
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
        Concept.set_ui_prefix("MSKCC")
        with open(self.content_file, "r") as f:
            # use counter as herb id
            for line in f:
                items = json.loads(line)
                print("currently processing: " + items["herb_name"])
                herb_atom = self.generate_atom(items["herb_name"],
                                               True, "PT")
                # scientific_name
                sn = items["scientific_name"]
                if sn == "":
                    pass
                sn = self.split_names(sn)
                sn_atom = self.generate_atom(sn, True, "SN")
                # common_name
                cn = items["common_name"]
                if cn == "":
                    pass
                cn = self.split_names(cn)
                cn_atom = self.generate_atom(cn, True, "CN")
                # build concept based on Common Name & Scientific name Atoms
                herb_atom.extend(sn_atom)
                herb_atom.extend(cn_atom)
                herb_concept = Concept("SDSI", atoms=herb_atom)
                # clinical_summary
                cs = items["clinical_summary"]
                herb_concept = self.generate_attr(herb_concept,
                                                  "Background", cs)
                # mechanism_of_action
                moa = items["mechanism_of_action"]
                herb_concept = self.generate_attr(herb_concept,
                                                  "Mechanism of Action", moa)
                # warnings
                warn = items["warnings"]
                herb_concept = self.generate_attr(herb_concept,
                                                  "Safety", warn)
                # purported_uses
                pu = items["purported_uses"]
                pu = self.split_content(pu)
                if len(pu) > 1:
                    for each in pu:
                        herb_concept = self.generate_idisk_schema(
                                        each, "SY", False,
                                        "DIS", "effects_on",
                                        herb_concept)
                # adverse_reactions
                ar = items["adverse_reactions"]
                ar = self.split_content(ar)
                if len(ar) > 1:
                    for each in ar:
                        herb_concept = self.generate_idisk_schema(
                                        each, "SY", False,
                                        "SS",
                                        "has_adverse_reaction",
                                        herb_concept)
                # herb-drug_interactions
                hdi = items["herb-drug_interactions"]
                hdi = self.remove_useless_for_HDI(hdi)
                hdi = self.split_content(hdi)
                if len(hdi) > 1:
                    for each in hdi:
                        herb_concept = self.generate_idisk_schema(
                                        each, "SY", False,
                                        "SPD", "interact_with",
                                        herb_concept)
                # write all concepts to local file
                self.write_to_local_file(herb_concept)

    def generate_atom(self, content, prefer_label, term_type):
        """
        Given the input, generate an iDISK Atom
        Return the generated iDISK Atom

        :param str content: the extracted content that needs to map to Atom
        :param bool prefer_label: whether or not the term is preferred
        :param str term_type: Atom term type
        :return: the generated iDISK Atom
        :rtype: list
        """
        # for HDI content, it's type must be list
        # content is either list or string, string could be empty, like ""
        atoms = []
        if isinstance(content, list):
            for each in content:
                if self.is_valid_content(each):
                    atom = Atom(each, src="MSKCC", src_id="0",
                                term_type=term_type,
                                is_preferred=prefer_label)
                    atoms.append(atom)
                else:
                    pass
        else:
            if self.is_valid_content(content):
                atom = Atom(content, src="MSKCC", src_id="0",
                            term_type=term_type,
                            is_preferred=prefer_label)
                atoms.append(atom)
            else:
                pass
        return atoms

    def generate_attr(self, herb_concept, attr_name, attr_value):
        """
        Given the content, transform it into Attribute

        :param idlib.Concept herb_concept: the concept that the Attribute is in
        :param str name: Attribute name for Concept
        :param str/list value: the content to transform into Attribute
        :rtype: idlib.Concept
        """
        if isinstance(attr_value, list):
            attr_value = " ".join(attr_value)
            atr = Attribute(herb_concept, attr_name, attr_value, src="MSKCC")
            herb_concept.attributes.append(atr)
            return herb_concept
        else:
            atr = Attribute(herb_concept, attr_name, attr_value, src="MSKCC")
            herb_concept.attributes.append(atr)
            return herb_concept

    def generate_rel(self, from_concept, to_concept,
                     rel_name):
        """
        Given the content, rel_name, edge concepts, generate Relationship

        :param Concept from_concept: the subject of this Relationship
        :param Concept to_concept: the object of this Relationship
        :param str rel_name: iDISK Relationship name
        :return: the subject and object Concept of this Relationship
        :rtype: tuple
        """
        rel = Relationship(subject=from_concept, obj=to_concept,
                           rel_name=rel_name, src="MSKCC")
        from_concept.relationships.append(rel)
        return (from_concept, to_concept)

    def generate_idisk_schema(self, value, value_type, prefer_label,
                              concept_type, rel_name, from_concept):
        """
        Given the herb content:
        1. generate its Atom,
        2. generate Concept based on Atom generated from step 1
        3. generate Relationship based on the Concept generated from step 2
        4. return the subject and object Concepts after building this schema

        :param str/list value: herb content
        :param str value_type: herb content Atom type
        :param bool prefer_label: whether or not the term is preferred
        :param str concept_type: Concept type for the generated Atom
        :param str rel_name: Relationship type given the generated Concept
        :param Concept from_concept: the subject Concept of this schema

        :return: the subject Concept of this Relationship
        :rtype: Concept
        """
        value_atom = self.generate_atom(value, prefer_label, value_type)
        value_concept = Concept(concept_type, atoms=value_atom)
        from_concept, value_concept = self.generate_rel(
                                            from_concept, value_concept,
                                            rel_name)
        self.write_to_local_file(value_concept)
        return from_concept


if __name__ == "__main__":
    args = parse_args()
    x = MSKCC_Converter(args.content_file, args.idisk_format_output)
    x.iterate_mskcc_file()
