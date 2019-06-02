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
        # list to store multiple concepts
        # TODO: discuss with Jake about storing options
        concepts = []
        count = 0
        with open(os.path.join(self.path, "cancer_ann_data.jsonl"), "r") as readFile:
            for line_number, line in enumerate(readFile):
                herb = json.loads(line)
                herb_id = line_number
                herb_name = herb["name"]
                # for each ingredient
                herb_atom = Atom(herb_name, src = "MSKCC", src_id = str(herb_id), 
                            term_type = "SY", is_preferred = True)
                # TODO: no definition for concept_type
                herb_concept = Concept.from_atoms([herb_atom], concept_type = "SDSI")
                annHDI = herb["annotated_HDI"]
                # HDI: interacts_with
                self.generateRelationship(herb_concept, annHDI, count, "interacts_with")
                # ADR: has_adverse_effect_on
                annADR = herb["annotated_ADR"]
                self.generateRelationship(herb_concept, annADR, count, "has_adverse_effect_on")

    # generate annotated HDI relationships for a single herb
    # @herb_concept: herb concept class from readFile function
    # @ann: list of annotated json object from cancer_ann_data.jsonl
    # @count: counter as src_id
    # @type: relationship type
    def generateRelationship(self, herb_concept, ann, count, type):
        if isinstance(ann, list):
            # remove empty entry
            ann = [x for x in ann if x != " "]
            herb_concept.attributes = []
            for each in ann:
                atom = Atom(each["term"], src = "MSKCC", 
                            src_id = str(count), term_type = "SY", is_preferred = True)
                count += 1
                hdi_concept = Concept.from_atoms([atom], concept_type = "SDSI")
                hdi_attr = Attribute(hdi_concept, atr_name = "annotated_HDI",
                                    atr_value = json.dumps(each), src = "UMLS")
                herb_concept.attributes.append(hdi_attr)
                hdi_rel = Relationship(herb_concept, hdi_concept, rel_name = type, src = "MSKCC")
                herb_concept.relationships.append(hdi_rel)
        else:
            pass


        

x = concept_driver()
x.readFile()
