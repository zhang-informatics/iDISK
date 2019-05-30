import urllib.request
import urllib.error
import urllib.parse
import json
import config
import os
import subprocess
import re


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
    # @annotations: the annotated document from BioPortal
    # @ar: herb["adverse_reactions"] content

    def getLabel(self, annotations, ar, get_class=True):
        labels = []
        for result in annotations:
            class_details = result["annotatedClass"]
            offset = result["annotations"][0]
            if get_class:
                try:
                    class_details = self.auth(
                        result["annotatedClass"]["links"]["self"])
                    ids = class_details["links"]["self"].split("%")[-1][2:]
                    d = {"term": class_details["prefLabel"], "id": ids, "source_db": "meddra", "original_string": offset["text"]}
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
    # @ar: data["adverse_reactions"]
    # return annotated terms

    def adrProcess(self, ar):
        if isinstance(ar, list):
            anno = []
            for each in ar:
                ar_annotations = self.auth(self.REST_URL + self.meddra + urllib.parse.quote(each) + self.conf)
                labels = self.getLabel(ar_annotations, each)
                if isinstance(labels, list):
                    anno.extend(labels)
                else:
                    anno.append(labels)
            return anno
        else:
            ar_annotations = self.auth(self.REST_URL + self.meddra + urllib.parse.quote(ar) + self.conf)
            labels = self.getLabel(ar_annotations, ar)
            return labels
    
    # check if content is none or empty
    # @content: herb["adverse_reactions"]
    # return true if content is either none or empty
    # otherwise return false
    def isBlank(self, content):
        if isinstance(content, list):
            content = list(filter(None, content))
            content = [each for each in content if each != " "]
            if not content:
                return False
            else:
                return True
        else:
            if content and content.strip():
                # content is not None AND content is not empty or blank
                return False
            # content is None OR content is empty or blank
            return True

    # AR annotation process main function
    # get AR content annotated using MEDDRA
    # @ar: AR content

    def main(self, ar):
        ar = self.remove(ar)
        if self.isBlank(ar):
            return " "
        else:
            anno = []
            res = self.adrProcess(ar)
            if isinstance(res, list):
                anno.extend(res)
            else:
                anno.append(res)
            # remove duplicate items
            final_anno = [value for index , value in enumerate(anno) if value not in anno[index+1:]]
            return final_anno
        
