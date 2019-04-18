import unittest
from set_functions import match, merge, intersection, union, difference


class TestMatch(unittest.TestCase):

    def setUp(self):
        self.test_pref_name1 = {"preferred_term": "Ginkgo",
                                "src": "DSLD",
                                "src_id": '1',
                                "term_type": "SY",
                                "synonyms": [],
                                "attributes": [],
                                "relationships": []}
        self.test_pref_name2 = {"preferred_term": "ginkgo",
                                "src": "NMCD",
                                "src_id": '2',
                                "term_type": "SN",
                                "synonyms": [],
                                "attributes": [],
                                "relationships": []}

        self.test_syns1 = {"preferred_term": "Ginkgo",
                           "src": "DSLD",
                           "src_id": '1',
                           "term_type": "SY",
                           "synonyms": [{"term": "gingko biloba"},
                                        {"term": "gin bil"}],
                           "attributes": [],
                           "relationships": []}

        self.test_syns2 = {"preferred_term": "Ginseng",
                           "src": "NMCD",
                           "src_id": '3',
                           "term_type": "SN",
                           "synonyms": [{"term": "Gingko Biloba"},
                                        {"term": "Schinseng"}],
                           "attributes": [],
                           "relationships": []}

        self.test_pref_syn1 = {"preferred_term": "Ginkgo",
                               "src": "DSLD",
                               "src_id": '1',
                               "term_type": "SY",
                               "synonyms": [{"term": "gingko biloba"},
                                            {"term": "ginseng"}],
                               "attributes": [],
                               "relationships": []}

        self.test_pref_syn2 = {"preferred_term": "Ginseng",
                               "src": "NMCD",
                               "src_id": '3',
                               "term_type": "SN",
                               "synonyms": [{"term": "Bingko Biloba"},
                                            {"term": "Schinseng"}],
                               "attributes": [],
                               "relationships": []}

    def test_match_pref_term(self):
        # "ginkgo" matches.
        matched = match(self.test_pref_name1, self.test_pref_name2)
        self.assertEqual(matched, set(["ginkgo"]))

    def test_match_synonym(self):
        # "gingko biloba" matches.
        matched = match(self.test_syns1, self.test_syns2)
        self.assertEqual(matched, set(["gingko biloba"]))

    def test_match_pref2syn(self):
        # "ginseng" matches.
        matched = match(self.test_pref_syn1, self.test_pref_syn2)
        self.assertEqual(matched, set(["ginseng"]))


class TestMerge(unittest.TestCase):

    def setUp(self):
        self.test_ing1 = {"preferred_term": "Ginkgo",
                          "src": "DSLD",
                          "src_id": '1',
                          "term_type": "SY",
                          "synonyms": [{"term": "gingko biloba",
                                        "src": "DSLD", "src_id": '1',
                                        "term_type": "SY",
                                        "is_preferred": False},
                                       {"term": "ginseng",
                                        "src": "DSLD", "src_id": '1',
                                        "term_type": "SY",
                                        "is_preferred": False}],
                          "attributes": [{"atr_name": "umls_semtype",
                                          "atr_val": "plnt"}],
                          "relationships": [{"rel_name": "interacts_with",
                                             "rel_val": "Codeine"}]
                          }

        self.test_ing2 = {"preferred_term": "Ginseng",
                          "src": "NMCD",
                          "src_id": '3',
                          "term_type": "SN",
                          "synonyms": [{"term": "Bingko Biloba",
                                        "src": "NMCD", "src_id": '3',
                                        "term_type": "SN",
                                        "is_preferred": False},
                                       {"term": "Schinseng",
                                        "src": "NMCD", "src_id": '3',
                                        "term_type": "SY",
                                        "is_preferred": False}],
                          "attributes": [{"atr_name": "category",
                                          "atr_val": "Chemical"}],
                          "relationships": [{"rel_name": "is_effective_for",
                                             "rel_val": "Cough"}]
                          }

        self.gold_merged = {"preferred_term": "Ginkgo",
                            "src": "DSLD",
                            "src_id": '1',
                            "term_type": "SY",
                            "synonyms": [{"term": "gingko biloba",
                                          "src": "DSLD", "src_id": '1',
                                          "term_type": "SY",
                                          "is_preferred": False},
                                         {"term": "ginseng",
                                          "src": "DSLD", "src_id": '1',
                                          "term_type": "SY",
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
                            }

    def test_merge(self):
        merged = merge(self.test_ing1, self.test_ing2)
        self.assertEqual(merged, self.gold_merged)


class TestSetFunctions(unittest.TestCase):

    def setUp(self):
        self.ings1 = [{"preferred_term": "Ginkgo",
                       "src": "DSLD",
                       "src_id": '1',
                       "term_type": "SY",
                       "synonyms": [{"term": "gingko biloba", "src": "DSLD",
                                     "src_id": '1', "term_type": "SY",
                                     "is_preferred": False},
                                    {"term": "ginseng", "src": "DSLD",
                                     "src_id": '1', "term_type": "SY",
                                     "is_preferred": False}],
                       "attributes": [{"atr_name": "umls_semtype",
                                       "atr_val": "plnt"}],
                       "relationships": [{"rel_name": "interacts_with",
                                          "rel_val": "Codeine"}]
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
                                     "is_preferred": False}],
                       "attributes": [{"atr_name": "umls_semtype",
                                       "atr_val": "plnt"}],
                       "relationships": [{"rel_name": "interacts_with",
                                          "rel_val": "Aspirin"}]
                       },
                      {"preferred_term": "5-htp",
                       "src": "DSLD",
                       "src_id": "20",
                       "term_type": "SY",
                       "synonyms": [{"term": "aloe vera", "src": "DSLD",
                                     "src_id": "20", "term_type": "SY",
                                     "is_preferred": False}],
                       "attributes": [{"atr_name": "umls_semtype",
                                       "atr_val": "chemical"}],
                       "relationships": [{"rel_name": "interacts_with",
                                          "rel_val": "creatine"}]
                       }
                      ]

        self.ings2 = [{"preferred_term": "Ginseng",
                       "src": "NMCD",
                       "src_id": '3',
                       "term_type": "SN",
                       "synonyms": [{"term": "Bingko Biloba",
                                     "src": "NMCD", "src_id": '3',
                                     "term_type": "SN",
                                     "is_preferred": False},
                                    {"term": "Schinseng",
                                     "src": "NMCD", "src_id": '3',
                                     "term_type": "SY",
                                     "is_preferred": False}],
                       "attributes": [{"atr_name": "category",
                                       "atr_val": "Chemical"}],
                       "relationships": [{"rel_name": "is_effective_for",
                                          "rel_val": "Cough"}]
                       },
                      {"preferred_term": "creatine",
                       "src": "NMCD",
                       "src_id": '8',
                       "term_type": "SY",
                       "synonyms": [{"term": "muscle juice", "src": "NMCD",
                                     "src_id": '8', "term_type": "SY",
                                     "is_preferred": False}],
                       "attributes": [{"atr_name": "umls_semtype",
                                       "atr_val": "chemical"}],
                       "relationships": []
                       },
                      {"preferred_term": "Euterpe Alocera",
                       "src": "NMCD",
                       "src_id": "33",
                       "term_type": "SY",
                       "synonyms": [{"term": "acee", "src": "NMCD",
                                     "src_id": "33", "term_type": "SY",
                                     "is_preferred": False}],
                       "attributes": [{"atr_name": "umls_semtype",
                                       "atr_val": "fruit"}],
                       "relationships": [{"rel_name": "has_therapeutic_class",
                                          "rel_val": "cardiovascular"}]
                       },
                      {"preferred_term": "Acai",
                       "src": "NMCD",
                       "src_id": '32',
                       "term_type": "SY",
                       "synonyms": [{"term": "acee", "src": "DSLD",
                                     "src_id": '3', "term_type": "SY",
                                     "is_preferred": False}],
                       "attributes": [{"atr_name": "umls_semtype",
                                       "atr_val": "plnt"},
                                      {"atr_name": "umls_semtype",
                                       "atr_val": "org"}],
                       "relationships": [{"rel_name": "interacts_with",
                                          "rel_val": "Aspirin"}]
                       },
                      ]

        self.gold_inter = [{"preferred_term": "Ginkgo",
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
                                          "is_preferred": True},
                                         {"term": "Acai", "src": "NMCD",
                                          "src_id": "32", "term_type": "SY",
                                          "is_preferred": True}],
                            "attributes": [{"atr_name": "umls_semtype",
                                            "atr_val": "plnt"},
                                           {"atr_name": "umls_semtype",
                                            "atr_val": "fruit"},
                                           {"atr_name": "umls_semtype",
                                            "atr_val": "org"}],
                            "relationships": [{"rel_name": "interacts_with",
                                               "rel_val": "Aspirin"},
                                              {"rel_name": "has_therapeutic_class",  # noqa
                                               "rel_val": "cardiovascular"}]
                            }
                           ]

        self.gold_union = [{"preferred_term": "Ginkgo",
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
                                          "is_preferred": True},
                                         {"term": "Acai",
                                          "src": "NMCD", "src_id": "32",
                                          "term_type": "SY",
                                          "is_preferred": True}],
                            "attributes": [{"atr_name": "umls_semtype",
                                            "atr_val": "plnt"},
                                           {"atr_name": "umls_semtype",
                                            "atr_val": "fruit"},
                                           {"atr_name": "umls_semtype",
                                            "atr_val": "org"}],
                            "relationships": [{"rel_name": "interacts_with",
                                               "rel_val": "Aspirin"},
                                              {"rel_name": "has_therapeutic_class",  # noqa
                                               "rel_val": "cardiovascular"}]
                            },
                           {"preferred_term": "5-htp",
                            "src": "DSLD",
                            "src_id": "20",
                            "term_type": "SY",
                            "synonyms": [{"term": "aloe vera", "src": "DSLD",
                                          "src_id": "20", "term_type": "SY",
                                          "is_preferred": False}],
                            "attributes": [{"atr_name": "umls_semtype",
                                            "atr_val": "chemical"}],
                            "relationships": [{"rel_name": "interacts_with",
                                               "rel_val": "creatine"}]
                            },
                           {"preferred_term": "creatine",
                            "src": "NMCD",
                            "src_id": '8',
                            "term_type": "SY",
                            "synonyms": [{"term": "muscle juice",
                                          "src": "NMCD", "src_id": '8',
                                          "term_type": "SY",
                                          "is_preferred": False}],
                            "attributes": [{"atr_name": "umls_semtype",
                                            "atr_val": "chemical"}],
                            "relationships": []
                            },
                           ]

        self.gold_diff = [{"preferred_term": "5-htp",
                           "src": "DSLD",
                           "src_id": "20",
                           "term_type": "SY",
                           "synonyms": [{"term": "aloe vera", "src": "DSLD",
                                         "src_id": "20", "term_type": "SY",
                                         "is_preferred": False}],
                           "attributes": [{"atr_name": "umls_semtype",
                                           "atr_val": "chemical"}],
                           "relationships": [{"rel_name": "interacts_with",
                                              "rel_val": "creatine"}]
                           },
                          {"preferred_term": "creatine",
                           "src": "NMCD",
                           "src_id": '8',
                           "term_type": "SY",
                           "synonyms": [{"term": "muscle juice", "src": "NMCD",
                                         "src_id": '8', "term_type": "SY",
                                         "is_preferred": False}],
                           "attributes": [{"atr_name": "umls_semtype",
                                           "atr_val": "chemical"}],
                           "relationships": []
                           },
                          ]

    def test_intersection(self):
        result = intersection(self.ings1, self.ings2)
        self.assertEqual(result, self.gold_inter)

    def test_union(self):
        result = union(self.ings1, self.ings2)
        self.assertEqual(result, self.gold_union)

    def test_difference(self):
        result = difference(self.ings1, self.ings2)
        self.assertEqual(result, self.gold_diff)


if __name__ == "__main__":
    unittest.main()
