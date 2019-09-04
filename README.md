# The integrated DIetary Supplements Knowledge base (iDISK)

## Overview
iDISK is a comprehensive knowledge base of dietary supplement ingredients, products, and related concepts.
This repository contains the source code required for building the knowledge base.


## Directory Structure

```
iDISK/                  # Top-level directory containing all iDISK related files. Set as the $IDISK_HOME environment variable.
  README.md             # This file.
  lib/                  # Functions and/or scripts common to every version of iDISK.
  sources/              # Contains the source databases. See below.
  versions/             # Contains directories containing different iDISK versions.
```

```
lib/
  idlib/                  # The iDISK API library. A Python package. See corresponding documentation for details.
  annotation/             # Scripts related to annotation of iDISK concepts and related data.
  mappers/                # Scripts for mapping iDISK concepts and related data to existing terminologies such as UMLS and MedDRA.
  filter_connections*.py  # Scripts for determining which concepts to merge.

sources/
  README.md               # File describing the general process for importing source databases into iDISK.
  NHP/                    # The name of the source database.
    08_01_2018/           # The date (MM_DD_YYYY) when the source files were downloaded.
      README.md           # Documentation for this download, including download URL, data version (if applicable), caveats, etc.
      download/           # Contains the downloaded data files in their original raw format.
      import/             # Contains the data files in a standard format for importing into iDISK.
        preprocess/       # Files containing any intermediary preprocessing moving from download/ to import/.
        concepts.jsonl    # The file containing the concepts to import into iDISK.
      scripts/            # Scripts for converting the source data in its raw format to the iDISK format.
    12_01_2017/
      .../
  DSLD/
    .../

versions/
  1.0.0/
    CHANGELOG.md	  # Changelog for this version of iDISK.
    concepts/		  # Contains the intermediate files generated to build iDISK.
    build/		  # Contains the final iDISK data files.
      Neo4j/		  # The Neo4j files corresponding to this version of iDISK.
      RRF/		  # The RRF files corresponding to this version of iDISK.
      .../		  # iDISK in other output formats as required.
```


## Initial setup

After cloning this repository, install `idlib`, the iDISK API library.
`idlib` is bundled with iDISK. Go to `lib/idlib` and follow the instructions in the README.

Edit the `PYTHON_INTERPRETER`, `IDISK_HOME`, and `IDISK_VERSION` variables in the
Project Configuration section of the `Makefile` as necessary for your installation. Then run,

```
make version
```

## The iDISK Schema

Firstly, make sure to 

```
source activate idisk
```

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


## Source Data

All source data for iDISK resides in the `sources/` directory. 
The rest of this guide assumes you have *properly* populated the `sources/` directory.
You can find a detailed example of how to do this at `sources/example_src`.

We'll check that the source data (i.e. the files belonging to the `SOURCE_FILES` variable
in the `Makefile`) is formatted properly. With the schema graph running, 

```
make check_contents
```

This will check each file against the schema to make sure all concepts, attributes, relationships, etc.
are properly formatted. This script will print out the number of found issues for each source data file
and write any issues to a a log file at `${source_file}.error`.


## Entity Linking

Any concept or relationship object that we want to link to an existing terminology should have
a `links_to` attribute in the schema, the value of which is a terminology. Each terminology
specified this way must also have an entry in `lib/idlib/idlib/entity_linking/annotator.conf`,
which specifies all `__init__` arguments to a Python class which does the entity linking to 
that terminology. This class should inherit from `EntityLinker` in
`lib/idlib/idlib/entity_linking/linkers.py`. For an example, see `MetaMapDriver` in the
aforementioned file.

First, ensure that the Neo4j schema graph is running. Then, create `annotator.conf`
as necessary to properly instantiate the corresponding `EntityLinker`
objects. Run entity linking by

```
make link_entities
```

This will likely take a few mintues. Check the progress in the log file at
`$(VERSION_DIR)/concepts/concepts_linked.jsonl.log`.


## Merging Synonymous Concepts

The next step is to generate candidate synonymy connections between the concepts in the source files.
Currently, two concepts are considered synonymous if they share one or more atom terms.

Note that for large numbers of concepts this can take a very long time,
so it is advisable that you run it in an environment in which you can set it and forget it.

```
make connections
```

These connections can be used directly, but it is advisable to filter them. Two methods of
filtering connections are implemented: The first removes connections based on some simple rules; the
second removes connections using human annotations.

To run the first method:

```
make filter_connections
```

--------------------------

### Annotating Synonyms

iDISK implements the Prodigy annotation tool for classifying connected pairs as one of the following labels:

* Equal
* Not Equal
* Parent-Child (i.e. the first concept is a hypernym of the second)
* Child-Parent (i.e. the first concept is a hyponym of the second)

If you are qualified to use Prodigy (it's not free) and have it installed (in the `idisk` virtual environment),
you can run the annotation task with:

```
make run_annotation
```

Once the annotation is complete, filter the connections according to the annotations with


```
make filter_connections_ann
```

--------------------------

Finally, now that we're confident in our connected concepts, we can merge them with

```
make merge
```


## Output Formats

The output of `make merge` is a JSON file in the iDISK format that is perfectly usable as a knowledge base within Python using the `idlib` API.

```python
from idlib import Concept
concepts = Concept.read_jsonl_file("path/to/version/concepts/concepts_merged.jsonl")
```

### Neo4j

Neo4j is a much better option for storing the knowledge base. To create the Neo4j version of iDISK, first create
an emtpy Neo4j graph. Then run

```
make neo4j
```

This command will populate the graph with the iDISK data elements. It will take a few minutes. 

### RRF

The  RRF data file format is alternative output format for iDISK. Used by the Unified Medical Language System (UMLS), it consists of a set of pipe-delimited
flat files: `MRSTY.RRF` (the types of the concepts), `MRCONSO.RRF` (the atoms for each concept), `MRSAT.RRF` (the attributes), and `MRREL.RRF` (the relationships).
Create these files by running

```
make rrf
```

-------------------------
