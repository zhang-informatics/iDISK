import argparse
import logging

from linkers import MetaMapDriver, QuickUMLSDriver, \
                    BioPortalDriver, MedDRARuleBased


logging.getLogger().setLevel(logging.INFO)



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metamap", action="store_true", default=False,
                        help="Run MetaMap.")
    parser.add_argument("--quickumls", action="store_true", default=False,
                        help="Run QuickUMLS.")
    parser.add_argument("--bioportal", action="store_true", default=False,
                        help="Run BioPortal.")
    parser.add_argument("--meddra_rulebased", action="store_true",
                        default=False, help="Run MedDRA Rule Based.")
    args = parser.parse_args()
    return args


def print_all_candidates(all_candidates, log_func):
    for indoc in all_candidates.keys():
        log_func(str(indoc))
        for (matched_str, candidates) in all_candidates[indoc].items():
            for candidate in candidates:
                log_func(f" '{matched_str}': {candidate}")


def print_best_candidates(best_candidates, log_func):
    for indoc in best_candidates.keys():
        log_func(str(indoc))
        for (matched_str, candidate) in best_candidates[indoc].items():
            log_func(f" '{matched_str}': {candidate}")


def test_metamap():

    def _log(msg, level="info"):
        func = getattr(logging, level)
        msg = f"<test_metamap> " + msg
        func(msg)

    mm = MetaMapDriver(mm_bin="/Users/vasil024/tools/MetaMap/public_mm/bin",
                       data_year="2016AA", data_version="USABase",
                       keep_semtypes=["dsyn", "neop", "fndg", "sosy", "vita"],
                       min_score=800)

    queries = [("lkjsdlfkj", "dysuria"),
               (10924, "diabetes"),
               ("c1", "vitamin c"),
               ("009234", "Melanoma often co-occurs with cancer"),
               ("55", "Topical administration of aloe gel is considered safe but oral consumption of aloe can cause gastrointestinal upset and electrolyte abnormalities."),
               ("234", "According to Cerbe, Inc. the efficacy of 714X may decrease when administered concurrently with vitamin B12, vitamin E, and shark or bovine cartilage.")
               ]

    _log("Input:")
    _log(str(queries))
    _log("All Candidates")
    all_candidates = mm.link(queries)
    print_all_candidates(all_candidates, _log)

    _log("Best Candidates")
    best_candidates = mm.get_best_links(all_candidates)
    print_best_candidates(best_candidates, _log)


def test_quickumls():

    def _log(msg, level="info"):
        func = getattr(logging, level)
        msg = f"<test_quickumls> " + msg
        func(msg)

    _log("QuickUMLS")
    # Uncomment for the vanilla version of QuickUMLS
    qumls_path = "/Users/vasil024/tools/QuickUMLS/PreferredTermRankedInstall/"
    qumls = QuickUMLSDriver(quickumls_install=qumls_path,
                            min_score=0.7,
                            keep_semtypes=["T047", "T191", "T184", "T033", "T127"])

    queries = [("lkjsdlfkj", "dysuria"),
               (10924, "diabetes"),
               ("c1", "vitamin c"),
               ("009234", "Melanoma often co-occurs with cancer"),
               ("55", "Topical administration of aloe gel is considered safe but oral consumption of aloe can cause gastrointestinal upset and electrolyte abnormalities."),
               ("234", "According to Cerbe, Inc. the efficacy of 714X may decrease when administered concurrently with vitamin B12, vitamin E, and shark or bovine cartilage.")
               ]
    _log("Input:")
    _log(str(queries))
    _log("All Candidates")
    all_candidates = qumls.link(queries)
    print_all_candidates(all_candidates, _log)

    _log("Best Candidates")
    best_candidates = qumls.get_best_links(all_candidates)
    print_best_candidates(best_candidates, _log)


def test_bioportal():

    def _log(msg, level="info"):
        func = getattr(logging, level)
        msg = f"<test_bioportal> " + msg
        func(msg)

    _log("BioPortal")
    bioportal = BioPortalDriver(
            rest_url="http://data.bioontology.org",
            query_url="/annotator?ontologies=http://data.bioontology.org/ontologies/MEDDRA&text=",  # noqa
            query_options="&longest_only=true&exclude_numbers=false&whole_word_only=true&exclude_synonyms=false&expand_class_hierarchy=true&class_hierarchy_max_level=999",  # noqa
            api_key="92922ecc-2f47-4b7e-b67b-9770c35d6b2d")

    queries = [("4", "dysuria"),
               ("10924", "diabetes"),
               ("009234", "Melanoma often co-occurs with cancer"),
               ("55", "Topical administration of aloe gel is considered safe but oral consumption of aloe can cause gastrointestinal upset and electrolyte abnormalities."),
               ("55.1", "blood electrolytes")
               ]

    _log("Input:")
    _log(str(queries))
    _log("All Candidates")
    all_candidates = bioportal.link(queries)
    print_all_candidates(all_candidates, _log)

    _log("Best Candidates")
    best_candidates = bioportal.get_best_links(all_candidates)
    print_best_candidates(best_candidates, _log)


def test_meddra_rulebased():

    def _log(msg, level="info"):
        func = getattr(logging, level)
        msg = f"<test_meddra_rulebased> " + msg
        func(msg)

    _log("MedDRA Rule Based")
    meddra = MedDRARuleBased()

    queries = [("1", "Renal"),
               ("2", "Cardiovascular"),
               ("3", "genitourinary")]
    _log("Input:")
    _log(str(queries))
    _log("All Candidates")
    all_candidates = meddra.link(queries)
    print_all_candidates(all_candidates, _log)

    _log("Best Candidates")
    best_candidates = meddra.get_best_links(all_candidates)
    print_best_candidates(best_candidates, _log)


if __name__ == "__main__":
    args = parse_args()
    if args.metamap is True:
        test_metamap()
    if args.quickumls is True:
        test_quickumls()
    if args.bioportal is True:
        test_bioportal()
    if args.meddra_rulebased is True:
        test_meddra_rulebased()
