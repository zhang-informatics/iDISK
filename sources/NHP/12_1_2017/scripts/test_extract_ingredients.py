import unittest
import numpy as np
import pandas as pd

from extract_ingredients import get_synonym, format_as_jsonl


class TestGetSynonym(unittest.TestCase):

    def setUp(self):
        self.row = {"ingredient_id": '1',
                    "proper_name": "Ginkgo Biloba",
                    "proper_name_f": "Gink Bil",
                    "common_name": "Gingko",
                    "common_name_f": "Ging"}

        self.row_none = {"ingredient_id": '1',
                         "proper_name": "Ginkgo Biloba",
                         "proper_name_f": "Gink Bil",
                         "common_name": None,
                         "common_name_f": "Ging"}

        self.row_empty = {"ingredient_id": '1',
                          "proper_name": "Ginkgo Biloba",
                          "proper_name_f": "Gink Bil",
                          "common_name": "",
                          "common_name_f": "Ging"}

        self.gold_synonyms = {"proper_name_f": {"term": "Gink Bil",
                                                "src": "NHPID",
                                                "src_id": '1',
                                                "term_type": "SN",
                                                "is_preferred": False},
                              "common_name": {"term": "Gingko",
                                              "src": "NHPID",
                                              "src_id": '1',
                                              "term_type": "SY",
                                              "is_preferred": False},
                              "common_name_f": {"term": "Ging",
                                                "src": "NHPID",
                                                "src_id": '1',
                                                "term_type": "SY",
                                                "is_preferred": False},
                              }

        self.gold_synonyms_none = {"proper_name_f": {"term": "Gink Bil",
                                                     "src": "NHPID",
                                                     "src_id": '1',
                                                     "term_type": "SN"},
                                   "common_name": None,
                                   "common_name_f": {"term": "Ging",
                                                     "src": "NHPID",
                                                     "src_id": '1',
                                                     "term_type": "SY"}
                                   }

    def test_get_synonym_sn(self):
        synonym = get_synonym(self.row, "proper_name_f")
        self.assertEqual(synonym, self.gold_synonyms["proper_name_f"])

    def test_get_synonym_sy(self):
        synonym = get_synonym(self.row, "common_name")
        self.assertEqual(synonym, self.gold_synonyms["common_name"])

    def test_get_synonym_none(self):
        synonym = get_synonym(self.row_none, "common_name")
        self.assertEqual(synonym, self.gold_synonyms_none["common_name"])

    def test_get_synonym_empty(self):
        synonym = get_synonym(self.row_empty, "common_name")
        self.assertEqual(synonym, self.gold_synonyms_none["common_name"])


class TestFormatAsJSONL(unittest.TestCase):

    def setUp(self):
        self.df_test = pd.DataFrame({"ingredient_id": ['1', '2'],
                                     "proper_name": ["Acai", "Ginkgo"],
                                     "proper_name_f": ["Acai", "gink"],
                                     "common_name": [np.nan, "ginseng"],
                                     "common_name_f": ["acee", "gink"],
                                     "potency": ["", "1"]
                                     })
        self.json_gold = [{"preferred_term": "Acai", "src": "NHPID",
                           "src_id": '1', "term_type": "SN",
                           "synonyms": [{"term": "acee", "src": "NHPID",
                                         "src_id": '1', "term_type": "SY",
                                         "is_preferred": False}
                                        ],
                           "attributes": [], "relationships": []},
                          {"preferred_term": "Ginkgo", "src": "NHPID",
                           "src_id": '2', "term_type": "SN",
                           "synonyms": [{"term": "gink", "src": "NHPID",
                                         "src_id": '2', "term_type": "SN",
                                         "is_preferred": False},
                                        {"term": "ginseng", "src": "NHPID",
                                         "src_id": '2', "term_type": "SY",
                                         "is_preferred": False},
                                        {"term": "gink", "src": "NHPID",
                                         "src_id": '2', "term_type": "SY",
                                         "is_preferred": False}],
                           "attributes": [], "relationships": []}
                          ]

    def test_format_as_jsonl(self):
        jsonlines = list(format_as_jsonl(self.df_test))
        self.assertEqual(jsonlines, self.json_gold)

    def test_for_duplicates(self):
        jsonlines = list(format_as_jsonl(self.df_test))
        # terms is a list of (term, term_type) pairs.
        terms = [(syn["term"], syn["term_type"]) for line in jsonlines
                 for syn in line["synonyms"]]
        terms += [(line["preferred_term"], line["term_type"])
                  for line in jsonlines]
        self.assertEqual(len(terms), len(set(terms)))


if __name__ == "__main__":
    unittest.main()
