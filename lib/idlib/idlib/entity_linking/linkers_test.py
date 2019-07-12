from linkers import MetaMapDriver

mm = MetaMapDriver(mm_bin="/Users/vasil024/tools/metamap/public_mm/bin",
                   data_year="2016AA", data_version="USABase")

instrs = ["1|diabetes",
          "2|breast cancer",
          "3|tylenol"]

print("Input:")
print(instrs)
print()
print("All Candidates")
# all_candidates = {doc: {matched_str : [candidate_link, ...]}}
all_candidates = mm.link(instrs, term_processing=True)
for indoc in all_candidates.keys():
    print(indoc)
    for (matched_str, candidates) in all_candidates[indoc].items():
        for candidate in candidates:
            print(f" '{matched_str}': {candidate}")

print()

print("Best Candidates")
# best_candidates = {doc: {matched_str : candidate_link}
best_candidates = mm.get_best_links(all_candidates, min_score=800)
for indoc in best_candidates.keys():
    print(indoc)
    for (matched_str, candidate) in best_candidates[indoc].items():
        print(f" '{matched_str}': {candidate}")

print("=======================\n")


instrs = ["1|Vitamin C is good for headaches.",
          "2|Side effects include nausea and vomiting."]
keep_semtypes = {"1": ["sosy", "vita"], "2": ["sosy"]}

print("Input:")
print(instrs)
print()
print("All Candidates")
all_candidates = mm.link(instrs, keep_semtypes=keep_semtypes,
                         term_processing=False)
for indoc in all_candidates.keys():
    print(indoc)
    for (matched_str, candidates) in all_candidates[indoc].items():
        for candidate in candidates:
            print(f" '{matched_str}': {candidate}")

print()

print("Best Candidates")
best_candidates = mm.get_best_links(all_candidates, min_score=600)
for indoc in best_candidates.keys():
    print(indoc)
    for (matched_str, candidate) in best_candidates[indoc].items():
        print(f" '{matched_str}': {candidate}")
