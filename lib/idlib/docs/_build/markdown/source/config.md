# idlib.config

This module defines the following variables:

## SOURCES

The valid source codes for building iDISK. These are

* IDISK: The Integrate Dietary Supplement Knowledge Base

* NMCD: Natural Medicines Comprehensive Database

* DSLD: Dietary Supplements Label Database

* NHPID: Natural Health Products Ingredient Database

* LNHPD: Licensed Natural Health Products Database

* MSKCC: Memorial Sloan Kettering Cancer Center herb database

* UMLS: the Unified Medical Language System metathesaurus

* MEDDRA: Medical Dictionary of Regulatory Activities

## TERM_TYPES

The valid term types for Atoms in iDISK. These are

* PN: Preferred Name (deprecated, use PT instead)

* PT: Preferred Term (the preferred term for this concept in a given source)

* SN: Scientific Name (e.g. the full chemical name or the taxonomic name)

* CN: Common Name (how people normally refer to this concept)

* SY: Synonym (generic term type. covers the cases when SN and CN cannot be determined)

## CONCEPT_TYPES

The valid Concept types in iDISK. These are

* SDSI: Semantic Dietary Supplement Ingredient

* DSP: Dietary Supplement Product

* SPD: Semantic Pharmacological Drug

* DIS: Disease

* TC: Therapeutic Class

* SOC: System Organ Class

* SS: Signs / Symptoms
