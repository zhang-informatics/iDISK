# The integrated DIetary Supplements Knowledge base (iDISK)

## Overview
iDISK is a comprehensive knowledge base of dietary supplement ingredients, products, and related concepts.
This repository contains the source code required for building the knowledge base. The current version of the
knowledge base, in both Neo4j and RRF formats, is available for download at <https://doi.org/10.13020/d6bm3v>
or from the [releases](https://github.com/jvasilakes/idisk/releases).

### Citing iDISK
Rizvi, Rubina F; Vasilakes, Jake A; Adam, Terrence J; Melton, Genevieve B; Bishop, Jeffrey R; Tao, Cui; Zhang, Rui. (2019). Integrated Dietary Supplement Knowledge Base (iDISK). Retrieved from the Data Repository for the University of Minnesota, https://doi.org/10.13020/d6bm3v.

A corresponding journal article is forthcoming.


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
Before getting started, run

```
source activate idisk
```


Copy `Makefile.example` to a nice, project-specific name like `Makefile.myproject`. Then, in the new Makefile,
edit the variables under the `PROJECT CONFIGURATION` section as necessary for your project and your working environment.
Then run,

```
make version
```

**N.B.** If this is not the first ever version of the database, you are encouraged to fill out the changelog location at `${IDISK_HOME}/versions/${VERSION_DIR}/CHANGELOG.md` with any changes or additions over the previous version.


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

### A Note about Config Files 

This project is specified by a few config files in `lib/config/`. The main config file to consider is
`kb.ini`, which, in addition to the schema, specifies certain constraints that apply to the data in each version iDISK.
The constraints are: 1) accepted data sources, 2) accepted term types, and 3) the concept types

`schemas.ini` works alongside the Cypher schemas in `lib/config/schemas/` to manage schema instances in Neo4j.


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

Any concept or relationship object that we want to link to an existing terminology must have
a `links_to` attribute in the schema, the value of which is an entry in `lib/config/linkers.conf`.
Each entry in `linkers.conf` specifies the required parameters to instantiate an
`idlib.entity_linking.linkers.EntityLinker`, the name of which is given by the `"class_name"` attribute.
For example, in schema 1.0.0 the `links_to` attribute of the PD (pharmaceutical drug) concepts is
`umls.quickumls.pd`. The entry under `umls.quickumls.pd` in `lib/config/linkers.conf` has the
`"class_name": QuickUMLSDriver`, which is the corresponding class name, while the remaining attributes
specify the arguments to instantiate a `QuickUMLSDriver`.

First, ensure that the Neo4j schema graph is running. Then, create or edit `linkers.conf`
as necessary to properly instantiate the corresponding `EntityLinker` classes. Run entity linking by

```
make link_entities
```

This will likely take a few mintues. Check the progress in the log file at
`$(VERSION_DIR)/concepts/concepts_linked.jsonl.log`.


## Merging Synonymous Concepts

The next step is to generate candidate synonymy connections between the concepts in the source files.
This is implemented in two steps. The first is focused on recall, generating a candidate connection
between two concepts if they share one or more atom terms. This step is run by,

```
make connections
```

Note that if there are any concept types that you do not want to consider matching, this can
be specified in the Makefile via the `--ignore_concept_types` option in the `connections` recipe.
Currently, supplement products (concept type DSP) are ignored.

These connections can be used directly, but it is advisable to filter them to improve precision.
Two methods of filtering connections are implemented: The first removes connections based on some simple rules
(specifically, the two concepts must be linked to the same entry in an external terminology in the previous step);
the second removes connections using human annotations.

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
>>> import idlib
>>> kb = idlib.load_kb("path/to/version/directory")
>>> 
>>> for rel in kb[0].get_relationships():
...     print(rel)
...     for rel2 in rel.object.get_relationships():
...         print(rel2)
...         break
...     break
NMCD0001213: 5-HTP 50 mg **has_ingredient** NHPID_DSLD_NMCD_MSKCC0482236: 5-Hydroxytryptophan
NHPID_DSLD_NMCD_MSKCC0482236: 5-Hydroxytryptophan **interacts_with** NMCD0478448: Tramadol
```

### Neo4j

Neo4j is a much better option for storing and using the knowledge base. To create the Neo4j version of iDISK, first create
an emtpy Neo4j graph. Then run

```
make neo4j
```

This command will populate the graph with the iDISK data elements. It will take a few minutes. Once the database is populated it can be exported by running

```
bin/neo4j-admin dump --database=graph.db --to=/absolute/path/to/destination/idisk-neo4j-<version>-<year>-<month>-<date>.dump
```

In the Neo4j Terminal tab.

### RRF

The  RRF data file format is alternative output format for iDISK. Used by the Unified Medical Language System (UMLS), it consists of a set of pipe-delimited
flat files: `MRSTY.RRF` (the types of the concepts), `MRCONSO.RRF` (the atoms for each concept), `MRSAT.RRF` (the attributes), and `MRREL.RRF` (the relationships).
Create these files by running

```
make rrf
```

This command will also create a date-stamped zip file containing the RRF files.

-------------------------
