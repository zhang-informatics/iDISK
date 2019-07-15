.. idlib documentation master file, created by
   sphinx-quickstart on Mon Jun 10 12:57:59 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The iDISK API Library (idlib)
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   source/data_elements
   source/set_functions
   source/config
   source/entity_linking


------------
Installation
------------

.. code-block:: bash

   make create_environment
   source activate idisk
   make requirements
   make idlib


-------------
Example Usage
-------------

>>> from idlib import Atom, Concept, Attribute, Relationship
>>> # Create the atoms that will make up this concept.
>>> terms = ["vitamin c", "ascorbic acid", "vitC"]
>>> atoms = []
>>> for (i, term) in enumerate(terms):
...	pref = True if term == "ascorbic acid" else False
...	atom = Atom(term, src="NMCD", src_id=str(i), term_type="SY", is_preferred=pref)
...	atoms.append(atom)
>>> concept = Concept(concept_type="SDSI", atoms=atoms)
>>> print(concept)
DC0000001: ascorbic acid
>>> # Give this concept an attribute.
>>> atr = Attribute(concept, atr_name="information",
...		    atr_value="Found in oranges!", src="NMCD")
>>> print(atr)
DC0000001: ascorbic acid *info* Found in oranges
>>> concept.add_elements(atr)
>>> # Create a synonymous concept2 and link them with a "same_as" relation.
>>> concept2 = Concept(concept_type="SDSI", atoms=atoms[:2])
DC0000002: ascorbic acid
>>> rel = Relationship(subject=concept, obj=concept2, rel_name="same_as", src="NMCD")
>>> concept.add_elements(rel)
>>> print(rel)
DC0000001: ascorbic acid *same_as* DC0000002: ascorbic acid
>>> # Note that the obj of a Relationship can be a str.
>>> rel_str = Relationship(subject=concept, obj="Orange", rel_name="found_in", src="NMCD")
>>> print(rel_str)
DC0000001: ascorbic acid *found_in* Orange
>>> # Relationships can also have attributes
>>> rel_attr = Attribute(rel, atr_name="confidence", atr_value="High", src="NMCD")
>>> rel_str.add_elements(rel_attr)


It is often the case that there are synonymous concepts, i.e. two or more concepts
that have overlapping atom terms. The `set_functions` module can be used to compute
the union of some lists of concepts. For example:


>>> from idlib import Atom, Concept, Attribute, Relationship
>>> from idlib.set_functions import Union
>>> # Let's create some unifiable concepts.
>>> terms1 = ["vitamin c", "ascorbic acid", "vitC"]
>>> atoms1 = []
>>> for (i, term) in enumerate(terms1):
...	pref = True if term == "vitC" else False
...	atom = Atom(term, src="NMCD", src_id=str(i), term_type="SY", is_preferred=pref)
...	atoms1.append(atom)
>>> concept1 = Concept(concept_type="SDSI", atoms=atoms1)
>>> terms2 = ["vitamin c", "C", "vitC", "Orange Juice"]
>>> atoms2 = []
>>> for (i, term) in enumerate(terms2):
...	pref = True if term == "vitC" else False
...	atom = Atom(term, src="NMCD", src_id=str(i), term_type="SY", is_preferred=pref)
...	atoms2.append(atom)
>>> concept2 = Concept(concept_type="SDSI", atoms=atoms2)
>>> print(list(concept1.get_atoms()))
[('DA0000001' 'vitamin c' 'SY' 'NMCD' '0' 'False'),
 ('DA0000002' 'ascorbic acid' 'SY' 'NMCD' '1' 'False'),
 ('DA0000003' 'vitC' 'SY' 'NMCD' '2' 'True')]
>>> print(list(concept2.get_atoms()))
[('DA0000001' 'vitamin c' 'SY' 'NMCD' '0' 'False'),
 ('DA0000002' 'C' 'SY' 'NMCD' '1' 'False'),
 ('DA0000003' 'vitC' 'SY' 'NMCD' '2' 'True'),
 ('DA0000002' 'Orange Juice' 'SY' 'NMCD' '3' 'False')]
>>> # Compute the union of these two concepts.
>>> # Since the concepts share atoms, this should result in a single concept.
>>> # Note that if two concepts match (share one or more atom terms), they are merged.
>>> u = Union([concept1, concept2])
>>> print(len(u.result))
1
>>> print(list(u.result[0].get_atoms()))
[('DA0000008' 'vitamin C' 'SY' 'NMCD' '0' 'False'),
 ('DA0000009' 'C' 'SY' 'NMCD' '1' 'False'),
 ('DA0000010' 'vitC' 'SY' 'NMCD' '2' 'True'),
 ('DA0000011' 'Orange Juice' 'SY' 'NMCD' '3' 'False'),
 ('DA0000002' 'ascorbic acid' 'SY' 'NMCD' '1' 'False')]




Indices and tables
==================

* :ref:`genindex`
