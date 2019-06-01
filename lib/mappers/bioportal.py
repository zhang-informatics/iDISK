import urllib.request
import urllib.error
import urllib.parse
import json
import config
import os
import subprocess
import re
import csv
import pickle
from collections import Counter


class meddraAnn(object):
    def __init__(self):
        self.meddra = "/annotator?ontologies=http://data.bioontology.org/ontologies/MEDDRA&text="
        self.REST_URL = "http://data.bioontology.org"
        self.conf = "&longest_only=true&exclude_numbers=false&whole_word_only=true&exclude_synonyms=true "
        self.API_KEY = config.api_key
    # BioPortal login

    def auth(self, url):
        opener = urllib.request.build_opener()
        opener.addheaders = [('Authorization', 'apikey token=' + self.API_KEY)]
        return json.loads(opener.open(url).read())
    # get prefLabel from annotation
    # @ annotations: the annotated document from BioPortal

    def getLabel(self, annotations, get_class=True):
        labels = []
        for result in annotations:
            class_details = result["annotatedClass"]
            if get_class:
                try:
                    class_details = self.auth(
                        result["annotatedClass"]["links"]["self"])
                    id = class_details["links"]["self"].split("%")[-1][2:]
                    d = {"term": class_details["prefLabel"].lower(), "id": id, "source_db": "meddra", "original_string": class_details["prefLabel"]}
                    labels.append(d)
                except urllib.error.HTTPError:
                    print(f"Error retrieving {result['annotatedClass']['@id']}")
                    continue
        return labels

    # remove all non-ASCII characters in the content
    # remove contents inside of ()
    # @value: the content needs to be cleaned

    def remove(self, value):
        if isinstance(value, list):
            value = [re.sub(r'[^\x00-\x7F]+', " ", each) for each in value]
            value = [re.sub(r" ?\([^)]+\)", "", each) for each in value]
            return value
        else:
            value = re.sub(r'[^\x00-\x7F]+', " ", value)
            value = re.sub(r" ?\([^)]+\)", "", value)
            return value
    
    # concate list of string into single string
    # @value: content to be concated
    # @sep: separator, i.e. "\t", "\n", " "

    def concate(self, value, sep):
        if isinstance(value, list):
            return (sep.join(value))
        else:
            return value

    # adverse reactions pre-process
    # @ar: datac["adverse_reactions"]
    # return annotated terms

    def adrProcess(self, ar):
        # check if exists adverse_reactions section
        if ar:
            ar_annotations = self.auth(
                self.REST_URL + self.meddra + urllib.parse.quote(ar) + self.conf)
            labels = self.getLabel(ar_annotations)
            return labels
        else:
            return " "

    # AR annotation process main function
    # get AR content annotated using MEDDRA
    # @name: herb name
    # @ar: AR content
    # @meddra: MEDDRA constructor
    # @output_file: the local file name to write

    def main(self, ar):
        data = {}
        ar = self.remove(self.concate(ar, " "))
        # if ar is empty
        if not ar:
            d = [{"term": " ", "id": " ", "source_db": "meddra", "original_string": " "}]
            return d
        else:
            res = self.adrProcess(ar)
            if not res:
                d = [{"term": " ", "id": " ", "source_db": "meddra", "original_string": " "}]
                return d
            else:
                return res