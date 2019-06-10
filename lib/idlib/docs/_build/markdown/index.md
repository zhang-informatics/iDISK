<!-- idlib documentation master file, created by
sphinx-quickstart on Mon Jun 10 12:57:59 2019.
You can adapt this file completely to your liking, but it should at least
contain the root `toctree` directive. -->
# The iDISK API Library (idlib)

* idlib.base

  * Atom

  * Concept

  * Attribute

  * Relationship

* pall.config

  * SOURCES

  * TERM_TYPES

  * CONCEPT_TYPES


## Installation

```
make create_environment
source activate idisk
make requirements
make idlib
```

## Example Usage

```python
>>> from idlib import Atom, Concept, Attribute, Relationship
>>> # Create the atoms that will make up this concept.
>>> terms = ["vitamin c", "ascorbic acid", "vitC"]
>>> atoms = []
>>> for (i, term) in enumerate(terms):
...    pref = True if term == "ascorbic acid" else False
...    atom = Atom(term, src="NMCD", src_id=str(i), term_type="SY", is_preferred=pref)
...    atoms.append(atom)
>>> concept = Concept.from_atoms(atoms, concept_type="SDSI")
>>> print(concept)
DC0000001: ascorbic acid
>>> # Give this concept an attribute.
>>> atr = Attribute(concept, atr_name="information",
...            atr_value="Found in oranges!", src="NMCD")
>>> print(atr)
DC0000001: ascorbic acid *info* Found in oranges
>>> concept.attributes.append(atr)
>>> # Create a synonymous concept2 and link them with a "same_as" relation.
>>> concept2 = Concept.from_atoms(atoms[:2], concept_type="SDSI")
DC0000002: ascorbic acid
>>> rel = Relationship(subject=concept, obj=concept2, rel_name="same_as", src="NMCD")
>>> concept.relationships.append(rel)
>>> print(rel)
DC0000001: ascorbic acid *same_as* DC0000002: ascorbic acid
>>> # Note that the obj of a Relationship can be a str.
>>> rel_str = Relationship(subject=concept, obj="Orange", rel_name="found_in", src="NMCD")
>>> print(rel_str)
DC0000001: ascorbic acid *found_in* Orange
>>> # Relationships can also have attributes
>>> rel_atr = Attribute(rel, atr_name="confidence", atr_value="Good", src="NMCD")
>>> rel_str.attributes.append(rel_atr)
```

# Indices and tables

* Index
