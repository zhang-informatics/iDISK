from metamap import MetaMapDriver

mm = MetaMapDriver(mm_bin="/Users/vasil024/tools/metamap/public_mm/bin",
                   data_year="2016AA", data_version="USABase")

instrs = ["1|diabetes",
          "2|breast cancer",
          "3|tylenol"]

print("Input:")
print(instrs)
print()
candidates = mm.link(instrs, term_processing=True)
for indoc in candidates.keys():
    print(indoc)
    for matched_phrase in candidates[indoc].keys():
        print(f" '{matched_phrase}'")
        for candidate in candidates[indoc][matched_phrase]:
            print(f"    {candidate}")

print()
best_candidates = mm.get_best_links(candidates, min_score=800)
for indoc in best_candidates.keys():
    print(indoc)
    for (matched_phrase, cand) in best_candidates[indoc].items():
        print(f" '{matched_phrase}': {cand}")

print("=======================\n")


instrs = ["1|Vitamin C is good for headaches.",
          "2|Side effects include nausea and vomiting."]
keep_semtypes = {"1": ["sosy"], "2": ["sosy"]}

print("Input:")
print(instrs)
print()
candidates = mm.link(instrs, keep_semtypes=keep_semtypes, term_processing=False)
for indoc in candidates.keys():
    print(indoc)
    for matched_phrase in candidates[indoc].keys():
        print(f" '{matched_phrase}'")
        for candidate in candidates[indoc][matched_phrase]:
            print(f"    {candidate}")

print()
best_candidates = mm.get_best_links(candidates, min_score=600)
for indoc in best_candidates.keys():
    print(indoc)
    for (matched_phrase, cand) in best_candidates[indoc].items():
        print(f" '{matched_phrase}': {cand}")
