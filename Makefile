.PHONY: version_clean version connections run_annotation filter_connections filter_connections_ann merge

#################################################################################
# PROJECT CONFIGURATION (You can change these)                                  #
#################################################################################

# Your preferred Python.
PYTHON_INTERPRETER = python3
# Where iDISK is located.
IDISK_HOME = /Users/vasil024/Projects/InProgressProjects/dietary_supplements_refactor/iDISK
# The version of iDISK to build.
IDISK_VERSION = 1.0.0
# Configuration file specifying how to build the schema.
SCHEMA_VERSION = 1.0.0
SCHEMA_CONF_FILE := $(IDISK_HOME)/lib/schemas/schemas.ini
# Paths to the source ingredient concept files.
SOURCE_FILES := $(IDISK_HOME)/sources/NMCD/11_30_2018/import/concepts.jsonl \
	        $(IDISK_HOME)/sources/DSLD/10_22_2018/import/concepts.jsonl \
	        $(IDISK_HOME)/sources/NHP/12_1_2017/import/concepts.jsonl \
	        $(IDISK_HOME)/sources/MSKCC/05_29_2019/import/concepts.jsonl


#################################################################################
# GLOBALS (DON'T CHANGE THESE)                                                  #
#################################################################################

PROJECT_NAME = idisk
VERSION_DIR := $(IDISK_HOME)/versions/$(IDISK_VERSION)/


#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Remove this version
version_clean:
	rm -r $(VERSION_DIR)


## Remove all annotation files and Prodigy datasets.
clean_annotation:
	rm -r $(VERSION_DIR)/concepts/manual_review/indata
	rm $(VERSION_DIR)/concepts/manual_review/prodigy.json  # symlink
	prodigy drop concept_matching


## Create the directories for this version.
version:
	mkdir -p $(VERSION_DIR)/concepts/
	mkdir -p $(VERSION_DIR)/build/{Neo4j,UMLS}/
	cd $(VERSION_DIR) && ln -s $(IDISK_HOME)/lib .


## Create the iDISK schema as a neo4j graph
schema:
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/idlib/idlib/schema.py \
		--schema_version $(SCHEMA_VERSION) \
		--schema_conf_file $(SCHEMA_CONF_FILE)

## Link concepts to external terminologies
link_entities:
	@echo "cat $(SOURCE_FILES) > $(VERSION_DIR)/concepts/concepts_orig.jsonl" \
		> $(VERSION_DIR)/concepts/LOG
	@cat $(SOURCE_FILES) > $(VERSION_DIR)/concepts/concepts_orig.jsonl
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/idlib/idlib/entity_linking/run_entity_linking.py \
		--concepts_file $(VERSION_DIR)/concepts/concepts_orig.jsonl \
		--outfile $(VERSION_DIR)/concepts/concepts_linked.jsonl \
		--annotator_conf $(IDISK_HOME)/lib/idlib/idlib/entity_linking/annotator.conf \
		--uri localhost --user neo4j --password password \
		2> $(VERSION_DIR)/concepts/concepts_linked.jsonl.log &
	@echo "Running entity linking. Check $(VERSION_DIR)/concepts/concepts_linked.jsonl.log for progress."
	@echo "Linked concepts will be written to $(VERSION_DIR)/concepts/concepts_linked.jsonl" 


## Find candidate connections between concepts. This requires idlib to be installed.
## This will take a few hours for a large number of inputs.
connections:
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/idlib/idlib/set_functions.py find_connections \
		--infiles $(VERSION_DIR)/concepts/concepts_linked.jsonl \
		--outfile $(VERSION_DIR)/concepts/connections.csv


## Filter connections based on simple heuristics
filter_connections:
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/filter_connections_basic.py \
		--connections_file $(VERSION_DIR)/concepts/connections.csv \
		--concepts_file $(VERSION_DIR)/concepts/concepts_linked.jsonl \
		--outfile $(VERSION_DIR)/concepts/connections_new.csv
	@mv $(VERSION_DIR)/concepts/connections.csv $(VERSION_DIR)/concepts/connections_orig.csv
	@mv $(VERSION_DIR)/concepts/connections_new.csv $(VERSION_DIR)/concepts/connections.csv
	@echo "New connections written to \n\t $(VERSION_DIR)/concepts/connections.csv"
	@echo "Original connections at \n\t $(VERSION_DIR)/concepts/connections_orig.csv"


## Run annotation using Prodigy
run_annotation:
	# Create the annotation data in Prodigy JSON lines format.
	mkdir -p $(VERSION_DIR)/concepts/manual_review/indata
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/annotation/to_prodigy.py \
		--concepts_file $(VERSION_DIR)/concepts/concepts_orig.jsonl \
		--connections_file $(VERSION_DIR)/concepts/connections.csv \
		--outfile $(VERSION_DIR)/concepts/manual_review/indata/matches.jsonl
	# Create a dataset to hold the annotations if it doesn't exist.
	cd $(VERSION_DIR)/concepts/manual_review/
	[[ -f prodigy.json ]] || ln -s $(IDISK_HOME)/lib/annotation/prodigy_resources/prodigy.json . 
	prodigy stats -l | grep -q "concept_matching" && \
		echo "Prodigy dataset already exists. Make sure this is what you want." || \
		prodigy dataset concept_matching "Evaluate whether connected concepts are indeed synonymous."
	# Run annotation.
	prodigy compare concept_matching \
		$(VERSION_DIR)/concepts/manual_review/indata/matches.jsonl \
		$(IDISK_HOME)/lib/annotation/prodigy_resources/template.html \
		-F $(IDISK_HOME)/lib/annotation/prodigy_resources/recipe.py


## Filter connections according to annotations.
filter_connections_ann:
	# Save annotations to a file
	prodigy db-out concept_matching $(VERSION_DIR)/concepts/manual_review/annotations
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/annotation/filter_connections_ann.py \
		--connections_file $(VERSION_DIR)/concepts/connections.csv \
		--annotations_file $(VERSION_DIR)/concepts/manual_review/annotations/concept_matching.jsonl \
		--outfile $(VERSION_DIR)/concepts/connections_new.csv
	@mv $(VERSION_DIR)/concepts/connections.csv $(VERSION_DIR)/concepts/connections_orig.csv
	@mv $(VERSION_DIR)/concepts/connections_new.csv $(VERSION_DIR)/concepts/connections.csv
	@echo "New connections written to \n\t $(VERSION_DIR)/concepts/connections.csv $(VERSION_DIR)/concepts/connections.csv"
	@echo "Original connections at \n\t $(VERSION_DIR)/concepts/connections.csv $(VERSION_DIR)/concepts/connections_orig.csv"


## Merge matched concepts.
merge:
	$(PYTHON_INTERPRETER) $(IDISK_HOME)/lib/idlib/idlib/set_functions.py union \
		--infiles $(VERSION_DIR)/concepts/concepts_linked.jsonl \
		--connections $(VERSION_DIR)/concepts/connections.csv \
		--outfile $(VERSION_DIR)/concepts/concepts_merged.jsonl
	@echo "Merged concepts written to $(VERSION_DIR)/concepts/concepts_merged.jsonl"



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
