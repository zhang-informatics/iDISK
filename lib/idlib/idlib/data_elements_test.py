from pprint import pprint

from idlib import data_elements, set_functions


# Create the atoms that will make up this concept.
terms = ["vitamin c", "ascorbic acid", "vitC"]
atoms = []
for (i, term) in enumerate(terms):
    pref = True if term == "ascorbic acid" else False
    atom = data_elements.Atom(term, src="NMCD", src_id=str(i),
                                    term_type="SY", is_preferred=pref)
    atoms.append(atom)

concept = data_elements.Concept(concept_type="SDSI", atoms=atoms)
print("-> DC0000001: ascorbic acid")
print(concept)

# Give this concept an attribute.
atr = data_elements.Attribute(concept, atr_name="information",
                                    atr_value="Found in oranges!", src="NMCD")
print("-> DC0000001: ascorbic acid *info* Found in oranges!")
print(atr)
concept.add_elements(atr)

# Create a synonymous concept2 and link them with a "same_as" relation.
concept2 = data_elements.Concept(concept_type="SDSI", atoms=atoms[:2])
print("-> DC0000002: ascorbic acid")
print(concept2)

rel = data_elements.Relationship(subject=concept, object=concept2,
                                       rel_name="same_as", src="NMCD")
concept.add_elements(rel)
print("-> DC0000001: ascorbic acid *same_as* DC0000002: ascorbic acid")
print(rel)

# Note that the obj of a Relationship can be a str.
rel_str = data_elements.Relationship(subject=concept, object="Orange",
                                           rel_name="found_in", src="NMCD")
print("-> DC0000001: ascorbic acid *found_in* Orange")
print(rel_str)

# Relationships can also have attributes
rel_atr = data_elements.Attribute(rel, atr_name="confidence",
                                        atr_value="Good", src="NMCD")
rel_str.add_elements(rel_atr)


# Let's create some unifiable concepts.
terms1 = ["vitamin c", "ascorbic acid", "vitC"]
atoms1 = []
for (i, term) in enumerate(terms1):
    pref = True if term == "vitC" else False
    atom = data_elements.Atom(term, src="NMCD", src_id=str(i),
                                    term_type="SY", is_preferred=pref)
    atoms1.append(atom)
concept1 = data_elements.Concept(concept_type="SDSI", atoms=atoms1)
terms2 = ["vitamin c", "C", "vitC", "Orange Juice"]
atoms2 = []
for (i, term) in enumerate(terms2):
    pref = True if term == "vitC" else False
    atom = data_elements.Atom(term, src="NMCD", src_id=str(i),
                                    term_type="SY", is_preferred=pref)
    atoms2.append(atom)
concept2 = data_elements.Concept(concept_type="SDSI", atoms=atoms2)
print("""
 -> [('DA0000001' 'vitamin c' 'SY' 'NMCD' '0' 'False'),
 ->  ('DA0000002' 'ascorbic acid' 'SY' 'NMCD' '1' 'False'),
 ->  ('DA0000003' 'vitC' 'SY' 'NMCD' '2' 'True')]
 """)
pprint(list(concept1.get_atoms()))
print("""
 -> [('DA0000001' 'vitamin c' 'SY' 'NMCD' '0' 'False'),
 ->  ('DA0000002' 'C' 'SY' 'NMCD' '1' 'False'),
 ->  ('DA0000003' 'vitC' 'SY' 'NMCD' '2' 'True'),
 ->  ('DA0000002' 'Orange Juice' 'SY' 'NMCD' '3' 'False')]
 """)
pprint(list(concept2.get_atoms()))
# Compute the union of these two concepts.
# Since the concepts share atoms, this should result in a single concept.
# Note that if two concepts match, they are merged.
u = set_functions.Union([concept1, concept2])
print(len(u.result))
print("""
 -> [('DA0000008' 'vitamin C' 'SY' 'NMCD' '0' 'False'),
 -> ('DA0000009' 'C' 'SY' 'NMCD' '1' 'False'),
 -> ('DA0000010' 'vitC' 'SY' 'NMCD' '2' 'True'),
 -> ('DA0000011' 'Orange Juice' 'SY' 'NMCD' '3' 'False'),
 -> ('DA0000002' 'ascorbic acid' 'SY' 'NMCD' '1' 'False')]
 """)
pprint(list(u.result[0].get_atoms()))
