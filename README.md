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
  main.pdf		# The full documentation for iDISK.
  src/			# The source TeX files for compiling main.pdf.

lib/
  idlib/		  # The iDISK API library. A Python package. See corresponding documentation for details.
  annotation/		  # Scripts related to annotation of iDISK concepts and related data.
  mappers/		  # Scripts for mapping iDISK concepts and related data to existing terminologies such as UMLS and MedDRA.
  filter_connections*.py  # Scripts for determining which concepts to merge.

sources/
  README.md		  # File describing the general process for importing source databases into iDISK.
  NMCD/			  # The name of the source database.
    08_01_2018/		  # The date (MM_DD_YYYY) when the source files were downloaded.
      README.md		  # Documentation for this download, including download URL, data version (if applicable), caveats, etc.
      download/		  # Contains the downloaded data files in their original raw format.
      import/		  # Contains the data files in a standard format for importing into iDISK.
	preprocess/       # Files containing any intermediary preprocessing moving from download/ to import/.
        ingredients.jsonl # The file containing ingredients to import into iDISK.
        products.jsonl    # The file containing products to import into iDISK.
        ....jsonl	  # Other files containing concepts as required.
      scripts/		  # Scripts for converting the source data in its raw format to the iDISK format.
    12_01_2017/
      .../
  DSLD/
    .../

versions/
  1.0.0/
    CHANGELOG.md	  # Changelog for this version of iDISK.
    lib/ 		  # Symbolic link to ${IDISK_HOME}/lib
    scripts/		  # Contains additional scripts required to build this specific version of iDISK.
    concepts/		  # Contains the intermediate files generated to build iDISK.
      ingredients/	  # Contains all files and scripts for processing and matching ingredient concepts.
      products/		  # Contains all files and scripts for processing product concepts.
      .../		  # Directories for other concepts as required.
    build/		  # Contains the final iDISK data files.
      Neo4j/
      UMLS/
      .../
```


## File Format

All data processed between the `sources/[source]/[date]/import/preprocess` files
and the final iDISK tables (`/versions/[version]/tables/*.RRF`) must be a JSON lines
file (extension `.jsonl`) each line of which is in the following format:

```
{
 "ui": str,					      # A unique identifier for this concept of the format {src}{int:07}. E.g. NMCD0000001
 "concept_type": str, 				      # The iDISK type of this concept. E.g. 'SDSI'. See the iDISK schema for details.
 "synonyms": [{"term": str, 			      # Synonyms of this preferred_term.
               "src": str,
               "src_id": str,
	       "term_type": str,
	       "is_preferred": bool},         	      # Whether this term is the preferred term in the source.
	      {...}],
 "attributes": [{"atr_name": str,                     # Any extra information about this term. E.g. supplement type, uses, etc.
		 "atr_value": str,
		 "src": str},
		...}		      
# Relationships with this term as the subject. All objects will be mapped to an existing terminology, such as UMLS.
 "relationships": [{"rel_name": str,    	      # The name of this relationship 
                    "object": str, 	    	      # The object of this relationship
		    "src": str,       		      # Name of the source database for this relationship. 
                    "attributes": [{"atr_name": str,  # Any attributes of this relationship.
				    "atr_value": str,
				    "src": str}, {...}]
}
```

## Initial setup

After cloning this repository, install `idlib`, the iDISK API library.
`idlib` is bundled with iDISK: go to `lib/idlib` and follow the instructions in the README.

The rest of this guide assumes you have *properly* populated the `sources/` directory.
You can find a detailed example of how to do this at `sources/example_src`.

Edit the variables in the PROJECT CONFIGURATION section of the `Makefile` as necessary. Then run,

```
make version
```

The next step is to generate candidate connections between the concepts in the source files.
Note that for large numbers of concepts this can take a very long time,
so it is advisable that you run it in an environment in which you can set it and forget it,
such as MSI.

```
source activate idisk
make connections
```

These connections can either be used directly, but it is advisable to filter them. Two methods of
filtering connections are implemented: The first removes connections based on some simple rules; the
second removes connections using human annotations.

To run the first method:

```
make filter_connections
```

To run the second method, follow these instructions:
iDISK implements the Prodigy annotation tool for classifying connected pairs as one of the following labels:

* Equal
* Not Equal
* Parent-Child (i.e. the first concept is a hypernym of the second)
* Child-Parent (i.e. the first concept is a hyponym of the second)

If you are qualified to use Prodigy (it's not free) and have it installed (in the `idisk` environment),
you can run the annotation task with:

```
make run_annotation
```

Once the annotation is complete, filter the connections according to the annotations with

```
make filter_connections_ann
```

Finally, now that we're confident in our connected concepts, we can merge them.

```
make merge
```

## The iDISK Schema

iDISK is built using Neo4j, so the first step is to install the latest version of [Neo4j](https://neo4j.com/download/).
Neo4j is used both to define the iDISK schema as well as to hold the final database. Here, we discuss creating and using
a schema. Neo4j graphs are specified using a query language called Cypher and we've supplied a Cypher script for the
current iDISK schema at `lib/schemas/schema_1.0.0.cypher`.

**N.B.** Schema versions are specified using semantic versioning (major.minor.patch). The schema versions are distinct
from the iDISK versions. That is, if iDISK updates to a new version, the schema will not necessarily require updating.
However, a new schema version always necessitates a new iDISK version.

Once you've installed Neo4j, open Neo4j Desktop, create a new graph, and start it (leaving it empty for now).
Take note of the username, password, and BOLT URI for this graph and enter them into the schema configuration file at
`lib/schemas/schemas.ini`. Finally, run the following to create the schema graph:

```
make schema
```

Now, if you go back to Neo4j Desktop and open your graph in the Neo4j browser, you'll see it has been populated. You can
view the entire schema with the Cypher query `MATCH(n) RETURN(n)`.
