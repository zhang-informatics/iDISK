# create concept and atom class for structured annotated data
import os
import sys
import json
# imoprt iDISK api
path = os.path.dirname(os.getcwd())
path = path.split("iDISK")[0]
path = os.path.join(path, "iDISK/lib/idlib")
sys.path.insert(0, path)
#from idlib import Atom, Concept, Attribute, Relationship
from base import Atom, Concept, Attribute, Relationship
class concept_driver(object):
    def __init__(self):
        # find the path to cancer_ann_data.jsonl
        self.path = os.path.dirname(os.getcwd())
        self.path = os.path.join(self.path, "download")
    # read cancer_ann_data.jsonl file
    def readFile(self):
        # TODO: discuss with Jake about storing options
        with open(os.path.join(self.path, "cancer_ann_data.jsonl"), "r") as readFile:
            for line_number, line in enumerate(readFile):
                herb = json.loads(line)
                herb_id = line_number
                herb_name = herb["name"]
                # for each annotated HDI
                herb_atom = Atom(herb_name, src = "MSKCC", src_id = str(herb_id), 
                            term_type = "SY", is_preferred = True)
                # TODO: no definition for concept_type
                herb_concept = Concept.from_atoms([herb_atom], concept_type = "SDSI")
                annHDI = herb["annotated_HDI"]
                # HDI: interacts_with
                self.generateRelationship(herb_concept, annHDI, 
                                            "interacts_with", "UMLS")
                # ADR: has_adverse_effect_on
                annADR = herb["annotated_ADR"]
                self.generateRelationship(herb_concept, annADR, 
                                            "has_adverse_effect_on", "MEDDRA")

    # generate annotated HDI relationships for a single herb
    # @herb_concept: herb concept class from readFile function
    # @ann: list of annotated json object from cancer_ann_data.jsonl
    # @rel_type: relationship type
    # @src_type: srouce type, i.e. "UMLS" or "MEDDRA"
    def generateRelationship(self, herb_concept, ann, rel_type, src_type):
        if isinstance(ann, list):
            # remove empty entry
            ann = [x for x in ann if x != " "]
            # list to store Attribute Atoms
            attr_atoms = []
            for each in ann:
                atom = Atom(each["term"], src = "MSKCC", src_id = str(each["id"]), 
                            term_type = "SY", is_preferred = True)
                attr_atoms.append(atom)
            # generate Concept for the Atom(s)
            attr_concept = Concept.from_atoms(attr_atoms, concept_type = "SDSI")
            # generate Relationship for attr_concept Concept
            attr_rel = Relationship(subject = herb_concept, obj = attr_concept, 
                                    rel_name = rel_type, src = src_type)
            # add attr_rel to the original concept
            herb_concept.relationships = [attr_rel]
        else:
            pass

if __name__ == "__main__":
    x = concept_driver()
    x.readFile()
