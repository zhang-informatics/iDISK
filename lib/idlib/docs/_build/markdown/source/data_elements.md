# idlib.data_elements

## Atom


#### class idlib.data_elements.Atom(term, src, src_id, term_type, is_preferred, ui=None)
Bases: `idlib.data_elements.DataElement`

An Atom is an a unique string, source, source ID, and term type.
A collection of Atoms is a Concept.


* **Parameters**

    * **term** (*str*) – The string of this atom.

    * **src** (*str*) – The source code of where this atom was found.

    * **src_id** (*str*) – The ID of this atom in its source.

    * **term_type** (*str*) – The type of term. E.g. “SY” for synonym.

    * **is_preferred** (*bool*) – Whether this string is the preferred name
      in its source.

    * **ui** (*str*) – The iDISK unique identifier of this atom. Optional.



#### classmethod from_dict(data)
Create an Atom instance from a JSON string.
The JSON must be formatted:

```
{"term": str,
 "src": str,
 "src_id": str,
 "term_type": str,
 "is_preferred": bool}
```


* **Parameters**

    **data** (*dict*) – The JSON data to load.



* **Returns**

    Atom instance of data.



* **Return type**

    Atom



#### to_dict()
Return this atom as a dict. The output format is:

```
{"term": str,
 "src": str,
 "src_id": str,
 "term_type": str,
 "is_preferred": bool}
```

## Concept


#### class idlib.data_elements.Concept(concept_type, atoms=None, ui=None)
Bases: `idlib.data_elements.DataElement`

An iDISK concept.


* **Parameters**

    * **concept_type** (*str*) – The iDISK type of this concept.
      E.g. “SDSI”.

    * **atoms** (*list*) – List of synonyms for this concept. Each member
      must be an instance of Atom. Optional.

    * **ui** (*str*) – the iDISK CUI for this concept. Optional.



#### classmethod from_dict(data)
Creates a concept from a JSON object. The JSON object must have
the format:

```
{"ui": str,
 "concept_type": str,
 "synonyms": [{"term": str,
               "src": str,
               "src_id": str,
               "term_type": str,
               "is_preferred": bool}, {...}]
 "attributes": [{"atr_name": str,
                 "atr_value": str,
                 "src": str}, {...}]
 "relationships": [{"rel_name": str,
                    "object": str,
                    "src": str,
                    "attributes": [{"atr_name": str,
                                    "atr_value": str,
                                    "src": str}, {...}]
}
```


* **Parameters**

    **data** (*dict*) – Input JSON data.



* **Returns**

    Concept instance built from data.



* **Return type**

    Concept



#### preferred_atom()
The preferred term for this concept is the preferred term
from the highest ranking source. That is, the atom such that
atom[“src”] is the closest to the top of the SOURCES list
and atom[“is_preferred”] is True.


* **Return type**

    Atom



#### classmethod resolve_relationships()
When multiple Concept instances are created from a JSON lines file
and contain relationships that reference each other, we have to wait
until all concepts are created before the objects of the relationships
resolved into Relationship instances from their UIs. When this is the
case, this method should be run after creating all concept instances.


#### to_dict()
Return this concept as an OrderedDict in the iDISK JSON format.

```
{"ui": str,
 "concept_type": str,
 "synonyms": [{"term": str,
               "src": str,
               "src_id": str,
               "term_type": str,
               "is_preferred": bool}, {...}]
 "attributes": [{"atr_name": str,
                 "atr_value": str,
                 "src": str}, {...}]
 "relationships": [{"rel_name": str,
                    "object": str,
                    "src": str,
                    "attributes": [{"atr_name": str,
                                    "atr_value": str,
                                    "src": str}, {...}]
}
```


* **Returns**

    Dictionary in the iDISK JSON format.



* **Return type**

    OrderedDict


## Attribute


#### class idlib.data_elements.Attribute(subject, atr_name, atr_value, src)
Bases: `idlib.data_elements.DataElement`

An attribute of a concept or relationship.


* **Parameters**

    * **subject** (*Concept/Relationship*) – The subject of this attribute.

    * **atr_name** (*str*) – The name of this attribute. E.g. “has_background”.

    * **atr_value** (*str*) – The value of this attribute.

    * **src** (*str*) – The source code of where this attribute was found.



#### classmethod from_dict(data, subject)
Create an Attribute instance from data.
data must be a dict with the following format:

```
{"atr_name": str,
 "atr_value": str,
 "src": str}
```


* **Parameters**

    * **data** (*dict*) – Input dictionary

    * **subject** (*Concept/Relationship*) – Subject of this attribute.



* **Returns**

    Attribute instance



* **Return type**

    Attribute



#### to_dict(return_subject=False, verbose_subject=False)
Output this attribute as a dictionary, optionally with a subject.
The subject is optional to accord with the iDISK JSON format.

```
{"atr_name": str,
 "atr_value": str,
 "src": str}
```


* **Parameters**

    * **return_subject** (*bool*) – If True, the returned dict contains
      a “subject” key.

    * **verbose_subject** (*bool*) – If True and return_subject is True,
      the value of the “subject” key includes
      the ui, name, and source, instead of
      just the ui.



* **Returns**

    dictionary representation of this attribute.



* **Return type**

    dict


## Relationship


#### class idlib.data_elements.Relationship(subject, rel_name, obj, src)
Bases: `idlib.data_elements.DataElement`

A relationship between two concepts.


* **Parameters**

    * **subject** (*Concept*) – The subject of this relationship.

    * **rel_name** (*str*) – The relation. E.g. “ingredient_of”.

    * **obj** (*Concept/str*) – The object of this relationship. Can be a
      Concept instance or a concept UI.

    * **src** (*str*) – The source code of where this relationship was found.

    * **attributes** (*list**(**Attribute**)*) – Any attributes of this relationship.



#### classmethod from_dict(data, subject, concept_mapping=None)
Create an Relationship instance from data.
data must be a dict with the following format:

```
{"rel_name": str,
 "object": str,
 "src": str,
 "attributes": [{"atr_name": str,
                 "atr_value": str,
                 "src": str}, {...}]
}
```


* **Parameters**

    * **data** (*dict*) – Input dictionary

    * **subject** (*Concept*) – Subject of this relationship.

    * **concept_mapping** (*dict*) – Mapping from strings to concepts as
      {string: Concept}, where string
      is equal to data[“object”]. Optional.
      If None, the object UI is used instead
      of a Concept instance.



* **Returns**

    Relationship instance



* **Return type**

    Relationship



#### get_attributes(r_type='object', return_subject=False)
Return a generator over attributes of this relationship.


* **Parameters**

    * **str** (*r_type*) – The type of what to yield. Possible values
      are [“object”, “dict”] If “object”, yields
      Attribute objects. If “dict”, yields dicts.

    * **bool** (*return_subject*) – If True, the returned dict contains
      a “subject” key.



* **Returns**

    Generator over attributes



* **Return type**

    generator



#### to_dict(return_subject=False, verbose=False)
Output this relationship as a dictionary, optionally with a subject.
The subject is optional to accord with the iDISK JSON format.

```
{"rel_name": str,
 "object": str,
 "src": str}
```


* **Parameters**

    * **return_subject** (*bool*) – If True, the returned dict contains
      a “subject” key.

    * **verbose_subject** (*bool*) – If True and return_subject is True,
      the value of the “subject” key includes
      the ui, name, and source, instead of
      just the ui.



* **Returns**

    dictionary representation of this attribute.



* **Return type**

    dict
