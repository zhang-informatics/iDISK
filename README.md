# The integrated DIetary Supplements Knowledge base (iDISK)

## Overview
iDISK is a comprehensive knowledge base of dietary supplement ingredients, products, and related concepts.
This repository contains the source code required for building the knowledge base.


## Directory Structure

```
iDISK/			# Top-level directory containing all iDISK related files. Set as the $IDISK_HOME environment variable.
  README.md		# This file.
  doc/ 			# Contains all documentation for iDISK.
  lib/			# Functions and/or scripts common to every version of iDISK.
  sources/		# Contains the source databases. See below.
  versions/		# Contains directories containing different iDISK versions.

doc/
  main.pdf		# Full documentation for iDISK
  src/			# The source TeX files for compiling main.pdf.

lib/
  set_functions.py	# Functions for combining iDISK concepts.
  to_prodigy.py		# Conversion script from iDISK JSON lines format to the format expected by the Prodigy annotation tool.
  tests/	        # Unit tests for the above.

sources/
  README.md		  # File describing the general process for importing source databases into iDISK.
  NMCD/			  # The name of the source database.
    08_01_2018/		  # The date (MM_DD_YYYY) when the source files were downloaded.
      README.md		  # Documentation for this download, including download URL, data version (if applicable), caveats, etc.
      download/		  # Contains the downloaded data files in their original format.
      import/		  # Contains the data files in a standard format for importing into iDISK.
	preprocess/       # Files containing any intermediary preprocessing moving from download/ to import/.
      ingredients.jsonl   # The file containing ingredients to import into iDISK.
      products.jsonl  	  # The file containing products to import into iDISK.
      ....jsonl		  # Other files containing concepts as required.
      scripts/		  # Scripts required to import this version of this data source.
    12_01_2017/
      .../
  DSLD/
    .../

versions/
  1.0.0/
    CHANGELOG.md	  # Changelog for this version of iDISK.
    lib/ 		  # Symbolic link to ${IDISK_HOME}/lib
    scripts/		  # Contains additional scripts required to build this specific version of iDISK.
    build/		  # Contains the intermediate files generated to build iDISK.
      ingredients/	  # Contains all files and scripts for processing and matching ingredient concepts.
        manual_review/    # Contains all files and scripts related to the manual review of matched ingredients.
      products/		  # Contains all files and scripts for processing product concepts.
      .../		  # Directories for other concepts as required.
    tables/
      UMLS/
        CMD.LOG		  # Log of commands used to create the files in this directory.
        DSCONSO.RRF
        DSSTY.RRF
        DSSAT.RRF
        DSREL.RRF
      RDF/
```


## File Format

All data processed between the `sources/[source]/[date]/import/preprocess` files
and the final iDISK tables (`/versions/[version]/tables/*.RRF`) must be a JSON lines
file (extension `.jsonl`) each line of which is in the following format:

```
{
 "preferred_term": str,				      # The term (e.g. ingredient name).
 "src": str,	       		  	              # Name of the source database for this preferred_term.
 "src_id": str,	        			      # The ID of this preferred_term in its source database.
 "term_type": str,      			      # The term type (e.g. 'SY') for this term in its source.
 "synonyms": [{"term": str, 			      # Synonyms of this preferred_term.
               "src": str,
               "src_id": str,
		       "term_type": str,
		       "is_preferred": bool},         # Whether this term is the preferred term in the source.
		      {...}],
 "attributes": {"key": value, [...]}		      # Any extra information about this term. E.g. supplement type, uses, etc.
# Relationships with this term as the subject. All objects will be mapped to an existing terminology, such as UMLS.
 "relationships": [{"rel_name": str,    	      # The name of this relationship 
                    "rel_val": str,     	      # The value of the object of this relationship  
				    "src": str,       # Name of the source database for this relationship. 
                    "attributes": {"key": "value"}},  # Any attributes of this relationship.
                   {...}]
}
```

### Notes
 * `synonyms` does not include the `preferred_term`.
 * The script `union.py` scripts add synonyms from the non-preferred source to the `synonyms` field.
