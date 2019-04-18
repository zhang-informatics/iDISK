import unittest
from to_prodigy import to_prodigy, get_duplicates


class TestToProdigy(unittest.TestCase):

    def setUp(self):
        self.ingredients = [{"preferred_term": "Ginkgo",
                             "src": "DSLD",
                             "src_id": '1',
                             "term_type": "SY",
                             "synonyms": [{"term": "gingko biloba",
                                           "src": "DSLD", "src_id": '1',
                                           "term_type": "SY",
                                           "is_preferred": False},
                                          {"term": "ginseng", "src": "DSLD",
                                           "src_id": '1', "term_type": "SY",
                                           "is_preferred": False},
                                          {"term": "Bingko Biloba",
                                           "src": "NMCD", "src_id": '3',
                                           "term_type": "SN",
                                           "is_preferred": False},
                                          {"term": "Schinseng",
                                           "src": "NMCD", "src_id": '3',
                                           "term_type": "SY",
                                           "is_preferred": False},
                                          {"term": "Ginseng",
                                           "src": "NMCD", "src_id": '3',
                                           "term_type": "SN",
                                           "is_preferred": True}],
                             "attributes": [{"atr_name": "umls_semtype",
                                             "atr_val": "plnt"},
                                            {"atr_name": "category",
                                             "atr_val": "Chemical"}],
                             "relationships": [{"rel_name": "interacts_with",
                                                "rel_val": "Codeine"},
                                               {"rel_name": "is_effective_for",
                                                "rel_val": "Cough"}]
                             },
                            {"preferred_term": "Acai",
                             "src": "DSLD",
                             "src_id": '3',
                             "term_type": "SY",
                             "synonyms": [{"term": "acee", "src": "DSLD",
                                           "src_id": '3', "term_type": "SY",
                                           "is_preferred": False},
                                          {"term": "euterpe", "src": "DSLD",
                                           "src_id": '3', "term_type": "SN",
                                           "is_preferred": False},
                                          {"term": "acee", "src": "NMCD",
                                           "src_id": "33", "term_type": "SY",
                                           "is_preferred": False},
                                          {"term": "Euterpe Alocera",
                                           "src": "NMCD", "src_id": "33",
                                           "term_type": "SY",
                                           "is_preferred": True}],
                             "attributes": [{"atr_name": "umls_semtype",
                                             "atr_val": "plnt"},
                                            {"atr_name": "umls_semtype",
                                             "atr_val": "fruit"}],
                             "relationships": [{"rel_name": "interacts_with",
                                                "rel_val": "Aspirin"},
                                               {"rel_name": "has_therapeutic_class",  # noqa
                                                "rel_val": "cardiovascular"}]
                             }
                            ]

        self.prodigy_jsonl = [{"ing1": {"term": "Ginkgo", "src": "DSLD"},
                               "ing2": {"term": "Ginseng", "src": "NMCD"},
                               "matched_synonyms": ["ginseng"]},
                              {"ing1": {"term": "Acai", "src": "DSLD"},
                               "ing2": {"term": "Euterpe Alocera",
                                        "src": "NMCD"},
                               "matched_synonyms": ["acee"]}]

    def test_to_prodigy(self):
        prodigy_jsonl = [to_prodigy(ing) for ing in self.ingredients]
        self.assertEqual(prodigy_jsonl, self.prodigy_jsonl)


class TestGetDuplicates(unittest.TestCase):

    def setUp(self):
        self.testcase = [1, 1, 2, 3, 2, 5]
        self.duplicates = [1, 2]

    def test_get_duplicates(self):
        self.assertEqual(get_duplicates(self.testcase), self.duplicates)
