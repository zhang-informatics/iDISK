import urllib.request
import urllib.error
import urllib.parse
import json
import config
import re


"""
The class is for MEDDRA annotation, purely for adverse reaction annotation
If you need to change or add additional features,
please refer to BioPortal documentation to make suitable changes
"""


class MeddraAnn(object):
    """
    BioPortal MEDDRA constructor
    You should register BioPortal then put your API_KEY in config.py file
    config.py should be under the same folder as this file
    """
    def __init__(self):
        """
        MeddraAnn constructor
        """
        self.meddra = "/annotator?ontologies=http://data.bioontology.org/ontologies/MEDDRA&text="  # noqa
        self.REST_URL = "http://data.bioontology.org"
        # annotation setup, will be freshed under get_meddra_config function
        self.conf = ""
        # BioPortal api key
        self.API_KEY = config.api_key

    def get_meddra_config(self, longest_only=True, exclude_numbers=True,
                          exclude_synonyms=True, whole_word_only=True):
        """
        MEDDRA config generation

        :param bool longest_only: match longest only
        :param bool exclude_numbers: exclue numbers
        :param bool exclude_synonyms: execlue synonyms
        :param bool whole_word_only: ignore partial word mapping
        """
        if longest_only:
            self.conf += "&longest_only=true"
        if exclude_numbers:
            self.conf += "&exclude_numbers=true"
        if whole_word_only:
            self.conf += "&whole_word_only=true"
        if exclude_synonyms:
            self.conf += "exclude_synonyms=true"
        self.conf += " "

    def auth_to_bioportal(self, url):
        """
        BioPortal auth authentication
        Return the authenticated page
        """
        opener = urllib.request.build_opener()
        opener.addheaders = [('Authorization', 'apikey token=' + self.API_KEY)]
        return json.loads(opener.open(url).read())

    def get_annotation(self, annotations, ar, get_class=True):
        """
        get MEDDRA annotated term, prefLabel
        return a list of dict with annotated terms following the below format
        [{term: annotated_term, id: bioportal id,
         source_db: meddra, original_string: annotated term offset}, ...]

        :param dict annotations: BioPortal output JSON, reads as dict
        :param str ar: the content that needs to be annotated
        :return: a list of dict with annotated terms
        :rtype: list
        """
        labels = []
        for result in annotations:
            class_details = result["annotatedClass"]
            # get offset
            offset = result["annotations"][0]
            if get_class:
                try:
                    class_details = self.auth_to_bioportal(
                        result["annotatedClass"]["links"]["self"])
                    # get bioportal id
                    ids = class_details["links"]["self"].split("%")[-1][2:]
                    # form into dict
                    d = {"term": class_details["prefLabel"], "id": ids,
                         "source_db": "meddra",
                         "original_string": offset["text"]}
                    labels.append(d)
                except urllib.error.HTTPError:
                    print(f"Error retrieving {result['annotatedClass']['@id']}")  # noqa
                    continue
        return labels

    # remove all non-ASCII characters in the content
    # remove contents inside of ()
    # @value: the content needs to be cleaned

    def remove_useless_content(self, value):
        """
        remove useless content, i.e. non-ASCII char, content in ()
        return the cleaned content

        :param str/list value: the content that needs to be cleaned
        :return: the cleaned content in its original type
        :rtype: str/list
        """
        if isinstance(value, list):
            value = [re.sub(r'[^\x00-\x7F]+', " ", each) for each in value]
            value = [re.sub(r" ?\([^)]+\)", "", each) for each in value]
            return value
        else:
            value = re.sub(r'[^\x00-\x7F]+', " ", value)
            value = re.sub(r" ?\([^)]+\)", "", value)
            return value

    # adverse reactions pre-process
    # @ar: data["adverse_reactions"]
    # return annotated terms

    def get_annotation_process(self, ar):
        """
        the full MEDDRA annotation process
        for each item in the content,
        1. find its annotated term and offset
        2. save it to the dict
        3. save all annotated dict into list

        :param str/list ar: the content to be annotated
        :return: return a list that stores all annotated dict
        :rtype: list
        """
        if isinstance(ar, list):
            anno = []
            for each in ar:
                ar_annotations = self.auth_to_bioportal(self.REST_URL + self.meddra + urllib.parse.quote(each) + self.conf)  # noqa
                labels = self.get_annotation(ar_annotations, each)
                if isinstance(labels, list):
                    anno.extend(labels)
                else:
                    anno.append(labels)
            return anno
        else:
            ar_annotations = self.auth_to_bioportal(self.REST_URL + self.meddra + urllib.parse.quote(ar) + self.conf)  # noqa
            labels = self.get_annotation(ar_annotations, ar)
            return labels

    # check if content is none or empty
    # @content: herb["adverse_reactions"]
    # return true if content is either none or empty
    # otherwise return false
    def is_blank(self, content):
        """
        check if contentis none or empty

        :param str/list content: the content needs to check
        :return: if the content is blank, return True, otherwise return False
        :rtype: bool
        """
        if isinstance(content, list):
            content = list(filter(None, content))
            content = [each for each in content if each != " " or each != ""]
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

    def run(self, ar):
        """
        the main function for the class
        get ADR content annotated using MEDDRA and save to a list of dict

        :param str/list ar: ADR content, i.e. herb[a]: adr_content
        :return: a list of dict with annotated terms
        :rtype: list
        """
        ar = self.remove_useless_content(ar)
        if self.is_blank(ar):
            return " "
        else:
            anno = []
            res = self.get_annotation_process(ar)
            if isinstance(res, list):
                anno.extend(res)
            else:
                anno.append(res)
            # remove duplicate items
            final_anno = [value for index, value in enumerate(anno) if value not in anno[index+1:]]  # noqa
            return final_anno
