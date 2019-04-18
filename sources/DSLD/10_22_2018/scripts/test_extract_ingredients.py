import unittest
import pandas as pd
from collections import OrderedDict
from nltk.corpus import stopwords
from pandas.util.testing import assert_frame_equal

from extract_ingredients import expand_ingredients, split_synonyms, \
                                get_regexes, apply_regexes, merge_groups, \
                                format_as_jsonl


class TestSplitSynonyms(unittest.TestCase):
    """
    Acai, acai (euterpe oleracea) juice;acai
    becomes
    Acai, acai (euterpe oleracea) juice
    Acai, acai
    """
    def setUp(self):
        self.df_test = pd.DataFrame({"group_name": ["Acai", "Ginseng"],
                                     "group_id": [1, 2],
                                     "synonyms": ['""acai (euterpe oleracea)"";""acaee""', # noqa
                                                 "gingko"]
                                     })
        self.gold_df = pd.DataFrame(OrderedDict(
                                    {"group_name": ["Acai", "Acai", "Ginseng"],
                                     "group_id": ["1", "1", "2"],
                                     "synonym": ["acai (euterpe oleracea)",
                                                 "acaee",
                                                 "gingko"]
                                     }))

    def test_split(self):
        split = split_synonyms(self.df_test)
        assert_frame_equal(split.reset_index(drop=True),
                           self.gold_df.reset_index(drop=True))


class TestRegexes(unittest.TestCase):

    def setUp(self):
        self.regexes = get_regexes(["fruit", "dehydrated"])

        self.space_split_test = "cat dog  CAUTION"
        self.space_split_gold = "cat dog"

        self.rm_doses_test = "cat dog 2g bird2go 1,000 i.u. stat!"
        self.rm_doses_gold = "cat dog bird2go stat!"

        self.rm_ratios_test = "cat needs 1:100 solution stat!"
        self.rm_ratios_gold = "cat needs solution stat!"

        self.rm_rights_test = "CatVita(tm): Its the best(r)!"
        self.rm_rights_gold = "CatVita: Its the best!"

        self.rm_quoted_test1 = "'I' saw it"
        self.rm_quoted_gold1 = "I saw it"
        self.rm_quoted_test2 = "3,3'-dihydroxy-B-carotene-4,4'-dione"
        self.rm_quoted_gold2 = "3,3'-dihydroxy-B-carotene-4,4'-dione"

        self.rm_braces_test = "We gave him a {cat}?"
        self.rm_braces_gold = "We gave him a cat?"

        self.rm_stop_words_test = "from 20g of gingko"
        self.rm_stop_words_gold = "20g gingko"

        self.rm_filter_words_test = "This fruit plant is dehydrated (fruit)"
        self.rm_filter_words_gold = "This fruit plant is dehydrated"

        self.rm_punct_test = "CatVita: Its the best!"
        self.rm_punct_gold = "CatVita Its the best!"

        self.rm_num_test = "There are twenty-two (22) cats"
        self.rm_num_gold = "There are twenty-two cats"

        self.rm_empty_parens_test = "Left over: [] (.. ,) [ .]."
        self.rm_empty_parens_gold = "Left over: ."

    def test_space_split_re(self):
        regex = self.regexes[0]
        self.assertEqual(regex(self.space_split_test), self.space_split_gold)

    def test_rm_dose_re(self):
        regex = self.regexes[1]
        self.assertEqual(regex(self.rm_doses_test), self.rm_doses_gold)

    def test_rm_ratios_re(self):
        regex = self.regexes[2]
        self.assertEqual(regex(self.rm_ratios_test), self.rm_ratios_gold)

    def test_rm_rights_re(self):
        regex = self.regexes[3]
        self.assertEqual(regex(self.rm_rights_test), self.rm_rights_gold)

    def test_rm_quoted_re1(self):
        regex = self.regexes[4]
        self.assertEqual(regex(self.rm_quoted_test1), self.rm_quoted_gold1)

    def test_rm_quoted_re2(self):
        regex = self.regexes[4]
        self.assertEqual(regex(self.rm_quoted_test2), self.rm_quoted_gold2)

    def test_rm_braces_re(self):
        regex = self.regexes[5]
        self.assertEqual(regex(self.rm_braces_test), self.rm_braces_gold)

    def test_rm_stop_words_re(self):
        regex = self.regexes[6]
        self.assertEqual(regex(self.rm_stop_words_test),
                         self.rm_stop_words_gold)

    def test_rm_filter_words_re(self):
        regex = self.regexes[7]
        self.assertEqual(regex(self.rm_filter_words_test),
                         self.rm_filter_words_gold)

    def test_rm_punct_re(self):
        regex = self.regexes[8]
        self.assertEqual(regex(self.rm_punct_test), self.rm_punct_gold)

    def test_rm_num_re(self):
        regex = self.regexes[9]
        self.assertEqual(regex(self.rm_num_test), self.rm_num_gold)

    def test_rm_empty_parens_re(self):
        regex = self.regexes[10]
        self.assertEqual(regex(self.rm_empty_parens_test),
                         self.rm_empty_parens_gold)


class TestRegexPipeline(unittest.TestCase):

    def setUp(self):
        dose_forms_file = "/Users/vasil024/Projects/InProgressProjects/dietary_supplements/data/DSLD/dose_forms.txt"  # noqa
        plant_parts_file = "/Users/vasil024/Projects/InProgressProjects/dietary_supplements/data/DSLD/plant_parts.txt"  # noqa
        filter_words = [l.strip() for l in open(dose_forms_file)] + \
                       [l.strip() for l in open(plant_parts_file)] + \
                       stopwords.words("english")  # noqa
        self.regexes = get_regexes(filter_words)
        self.pipeline_test = ["1, 3, N-Dipropyl-7- Proparglyxanthine",
                              "3,3'-dihydroxy-B-carotene-4,4'-dione",
                              "from 15 mg of 100:1 Oil of Oregano",
                              "11% as Phosphatidyl Inositol",
                              "Advantra Z(R) fruit extract",
                              "Black Currant (Ribes nigrum) (fruit) extract",
                              "Aloe vera gel 200:1 ext.",
                              "American Ginseng (Panax quinquefolius) root extract 4:1"]  # noqa
        self.pipeline_gold = ["1, 3, N-Dipropyl-7- Proparglyxanthine",
                              "3,3'-dihydroxy-B-carotene-4,4'-dione",
                              "Oil Oregano",
                              "Phosphatidyl Inositol",
                              "Advantra Z fruit extract",
                              "Black Currant (Ribes nigrum) extract",
                              "Aloe vera gel ext.",
                              "American Ginseng (Panax quinquefolius) root extract"]  # noqa

    def test_pipeline(self):
        processed_strings = [apply_regexes(string, self.regexes)
                             for string in self.pipeline_test]
        self.assertEqual(processed_strings, self.pipeline_gold)


class TestExpandIngredients(unittest.TestCase):
    """
    1, Acai, acai (euterpe oleracea)  juice
    becomes
    Acai, acai juice
    Acai, euterpe oleracea
    """
    def setUp(self):
        self.df_test = pd.DataFrame({"group_name": ["Acai", "Acai", "Ginseng"],
                                     "group_id": ["1", "1", "2"],
                                     "synonym": ["acai (euterpe oleracea)",
                                                 "acaee",
                                                 "gingko"]
                                     })
        self.gold_df = pd.DataFrame(OrderedDict(
                                    {"group_name": ["Acai", "Acai",
                                                    "Acai", "Ginseng"],
                                     "group_id": ["1", "1", "1", "2"],
                                     "synonym": ["acai",
                                                 "euterpe oleracea",
                                                 "acaee",
                                                 "gingko"]
                                     }))

    def test_expand(self):
        expanded = expand_ingredients(self.df_test)
        assert_frame_equal(expanded.reset_index(drop=True),
                           self.gold_df.reset_index(drop=True))


class TestMergeGroups(unittest.TestCase):

    def setUp(self):
        self.df_test = pd.DataFrame({"group_name": ["Acai", "Acai", "Ginkgo"],
                                     "group_id": ["1", "1", "2"],
                                     "synonym": ["acai juice", "euterpe oleracea", "ginseng"]  # noqa
                                    })
        self.df_gold = pd.DataFrame({"group_name": ["Acai", "Ginkgo"],
                                     "group_id": ["1", "2"],
                                     "synonyms": [["acai juice", "euterpe oleracea"], ["ginseng"]]  # noqa
                                     })

    def test_merge_groups(self):
        assert_frame_equal(merge_groups(self.df_test), self.df_gold)


class TestFormatAsJSONL(unittest.TestCase):

    def setUp(self):
        self.df_test = pd.DataFrame({"group_name": ["Acai", "Ginkgo"],
                                     "group_id": ['1', '2'],
                                     "synonyms": [["acai juice",
                                                   "euterpe oleracea",
                                                   "acai juice"],
                                                  ["ginseng", "",
                                                   None, "gingko"]]
                                     })
        self.json_gold = [{"preferred_term": "Acai", "src": "DSLD",
                           "src_id": '1', "term_type": "SY",
                           "synonyms": [{"term": "acai juice", "src": "DSLD",
                                         "src_id": '1', "term_type": "SY",
                                         "is_preferred": False},
                                        {"term": "euterpe oleracea",
                                         "src": "DSLD", "src_id": '1',
                                         "term_type": "SY",
                                         "is_preferred": False}],
                           "attributes": [], "relationships": []},
                          {"preferred_term": "Ginkgo", "src": "DSLD",
                           "src_id": '2', "term_type": "SY",
                           "synonyms": [{"term": "ginseng", "src": "DSLD",
                                         "src_id": '2', "term_type": "SY",
                                         "is_preferred": False},
                                        {"term": "gingko", "src": "DSLD",
                                         "src_id": '2', "term_type": "SY",
                                         "is_preferred": False}],
                           "attributes": [], "relationships": []}
                          ]

    def test_format_as_jsonl(self):
        jsonlines = list(format_as_jsonl(self.df_test))
        self.assertEqual(jsonlines, self.json_gold)

    def test_for_duplicates(self):
        jsonlines = list(format_as_jsonl(self.df_test))
        terms = [(syn["term"], syn["term_type"]) for line in jsonlines
                 for syn in line["synonyms"]]
        terms += [(line["preferred_term"], line["term_type"])
                  for line in jsonlines]
        self.assertEqual(len(terms), len(set(terms)))


if __name__ == "__main__":
    unittest.main()
