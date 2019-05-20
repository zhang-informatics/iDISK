# The iDISK API (idlib)

This library contains classes for building and working with iDISK.

There are currently four classes representing the basic building blocks of iDISK:

* Atom
* Concept
* Attribute
* Relationship

### Example usage

```python
>>> from idlib import Atom, Concept
>>> terms = ["vitamin c", "ascorbic acid", "vitC"]
>>> atoms = []
>>> for (i, term) in enumerate(terms):
...	pref = True if term == "ascorbic acid" else False
...	atom = Atom(term, src="NMCD", src_id=str(i), term_type="SY", is_preferred=pref)
...	atoms.append(atom)
>>> concept = Concept.from_atoms(atoms, concept_type="SDSI")
>>> print(concept)
DC0000001: ascorbic acid
```
