# The iDISK API (idlib)

This library contains classes for building and working with iDISK.

There are currently four classes representing the basic building blocks of iDISK:

* Atom
* Concept
* Attribute
* Relationship

The possible source databases and term types are defined in idisk.ini. 

### Example usage

```python
>>> from idlib import Atom, Concept, Attribute, Relationship
>>> # Create the atoms that will make up this concept.
>>> terms = ["vitamin c", "ascorbic acid", "vitC"]
>>> atoms = []
>>> for (i, term) in enumerate(terms):
...	pref = True if term == "ascorbic acid" else False
...	atom = Atom(term, src="NMCD", src_id=str(i), term_type="SY", is_preferred=pref)
...	atoms.append(atom)
>>> concept = Concept.from_atoms(atoms, concept_type="SDSI")
>>> print(concept)
DC0000001: ascorbic acid
>>> # Give this concept an attribute.
>>> atr = Attribute(concept, atr_name="information",
...		    atr_value="Found in oranges!", src="NMCD")
>>> print(atr)
DC0000001: ascorbic acid *info* Found in oranges
>>> concept.attributes = [atr]
>>> # Create a synonymous concept2 and link them with a "same_as" relation.
>>> concept2 = Concept.from_atoms(atoms[:2], concept_type="SDSI")
DC0000002: ascorbic acid
>>> rel = Relationship(subject=concept, obj=concept2, rel_name="same_as", src="NMCD")
>>> concept.relationships = [rel]
>>> print(rel)
DC0000001: ascorbic acid *same_as* DC0000002: ascorbic acid
```
