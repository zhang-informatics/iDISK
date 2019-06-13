.PHONY: clean version connections run_annotation filter_connections merge

#################################################################################
# PROJECT CONFIGURATION (You can change these)                                  #
#################################################################################

# Your preferred Python.
PYTHON_INTERPRETER = python3
# Where iDISK is located.
IDISK_HOME = /Users/vasil024/Projects/InProgressProjects/dietary_supplements_refactor/iDISK
# The version of iDISK to build.
IDISK_VERSION = 1.0.0
# Paths to the source ingredient concept files.
SOURCE_FILES := $(IDISK_HOME)/sources/NMCD/11_30_2018/import/ingredients.jsonl \
	        $(IDISK_HOME)/sources/DSLD/10_22_2018/import/ingredients.jsonl \
	        $(IDISK_HOME)/sources/NHP/12_1_2017/import/ingredients.jsonl


#################################################################################
# GLOBALS (DON'T CHANGE THESE)                                                  #
#################################################################################

PROJECT_NAME = idisk
BUILD_DIR := $(IDISK_HOME)/versions/$(IDISK_VERSION)/


#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Remove this version
clean:
	rm -r $(BUILD_DIR)

## Create the directories for this version.
version:
	mkdir -p $(BUILD_DIR)/{ingredients,products}/
	cd $(BUILD_DIR) && ln -s $(IDISK_HOME)/lib .

## Find candidate connections between concepts. This requires idlib to be installed.
## This can take a few hours for a large number of inputs.
connections:
	@echo "cat $(SOURCE_FILES) > $(BUILD_DIR)/ingredients/all_ingredients.jsonl" > $(BUILD_DIR)/ingredients/LOG
	@cat $(SOURCE_FILES) > $(BUILD_DIR)/ingredients/all_ingredients.jsonl
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/idlib/idlib/set_functions.py \
		find_connections \
		--infiles $(SOURCE_FILES) \
		--outfile $(BUILD_DIR)/ingredients/connections.csv

## Run annotation using Prodigy
run_annotation:
	# Create the annotation data in Prodigy JSON lines format.
	mkdir -p $(BUILD_DIR)/ingredients/manual_review/indata
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/annotation/to_prodigy.py \
		--concepts_file $(BUILD_DIR)/ingredients/all_ingredients.jsonl \
		--connections_file $(BUILD_DIR)/ingredients/connections.csv \
		--outfile $(BUILD_DIR)/ingredients/manual_review/indata/matches.jsonl
	# Create a dataset to hold the annotations if it doesn't exist.
	cd $(BUILD_DIR)/ingredients/manual_review/
	[[ -f prodigy.json ]] || ln -s $(IDISK_HOME)/lib/annotation/prodigy_resources/prodigy.json . 
	prodigy stats -l | grep -q "concept_matching" || \
		prodigy dataset concept_matching "Evaluate whether connected concepts are indeed synonymous."
	# Run annotation.
	prodigy compare concept_matching \
		$(BUILD_DIR)/ingredients/manual_review/indata/matches.jsonl \
		$(IDISK_HOME)/lib/annotation/prodigy_resources/template.html \
		-F $(IDISK_HOME)/lib/annotation/prodigy_resources/recipe.py

## Filter connections according to annotations.
filter_connections:
	# Save annotations to a file
	prodigy db-out concept_matching $(BUILD_DIR)/ingredients/manual_review/annotations
	mv $(BUILD_DIR)/ingredients/connections.csv $(BUILD_DIR)/ingredients/connections_orig.csv
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/annotation/filter_connections.py \
		--connections_file $(BUILD_DIR)/ingredients/connections_orig.csv \
		--annotations_file $(BUILD_DIR)/ingredients/manual_review/annotations/concept_matching.jsonl \
		--outfile $(BUILD_DIR)/ingredients/connections.csv

## Merge matched concepts.
merge:
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/idlib/idlib/set_functions.py union \
		--infiles $(BUILD_DIR)/ingredients/all_ingredients.jsonl \
		--connections $(BUILD_DIR)/ingredients/connections.csv \
		--outfile $(BUILD_DIR)/ingredients/merged_ingredients.jsonl
						


#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
