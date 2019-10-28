import re
import weakref
import logging
import json
import numbers
import numpy as np

from copy import deepcopy
from collections import OrderedDict, defaultdict

try:
    from idlib.config import SOURCES, TERM_TYPES, CONCEPT_TYPES
except EnvironmentError:
    logging.warning("No config specified. Loading defaults.")
    SOURCES = TERM_TYPES = CONCEPT_TYPES = None


class DataElement(object):

    __refs__ = defaultdict(list)  # Holds all instances of each class
    _prefix = ""
    _counter = 0
    _ui_template = "{0}{1:07}"  # _prefix, _counter

    def __init__(self, ui=None):
        # This is distinct from _counter, as it holds the number of this
        # data element rather than the number of all data elements.
        self._number = 0
        # Containers. None means that it is not implemented for
        # this data element.
        self._atoms = None
        self._attributes = None
        self._relationships = None
        if ui is None:
            self._increment_counter()
            self.ui = self._ui_template.format(self._prefix, self._counter)
        else:
            self.ui = ui
            self.init_counter(int(ui.replace(self._prefix, "")))

    def _register(self):
        """
        Add this instance to __refs__. To be called at the end of __init__
        in any class that inherits from DataElement.
        """
        self.__refs__[self.__class__].append(weakref.ref(self))

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result

    # TODO: Handle recursive copying with Relationships.
    def __deepcopy__(self, memo):
        raise NotImplementedError()
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result

    @classmethod
    def get_instances(cls):
        """
        Get all instances of the Concept class.

        :returns: Generator over Concept instances.
        :rtype: generator
        """
        for inst_ref in cls.__refs__[cls]:
            inst = inst_ref()
            if inst is not None:
                yield inst

    @classmethod
    def set_ui_prefix(cls, prefix):
        """
        Set the string to prepend to the UI of each instance.

        :param str prefix: The prefix to set.
        """
        cls._prefix = prefix

    @classmethod
    def init_counter(cls, num):
        """
        Initialize the unique identifier counter with the given number.

        :param int num: The number to initialize with.
        """
        cls._counter = num

    @classmethod
    def _increment_counter(cls):
        """
        Increment the unique identifier counter by 1.
        """
        cls._counter += 1

    @property
    def ui(self):
        """
        The unique identifier is always dynamically determined by the
        values of self._prefix and self._number.
        """
        return self._ui_template.format(self._prefix, self._number)

    @ui.setter
    def ui(self, value):
        """
        The unique identifier is always dynamically determined by the
        values of self._prefix and self._number. However, the values of these
        hidden variables can be modified by using the UI setter.

        :param str value: The new unique identifier.
        """
        if not re.match(r'.+[0-9]{7}', value):
            msg = "UI must match the regex '.+[0-9]{7}'. E.g. DC0000001."
            raise ValueError(msg)
        self._number = int(value[-7:])
        self._prefix = value[:-7]

    def add_elements(self, elements):
        """
        Add a collection of elements to this data element if it does not
        already belong to it. Each element must be an Atom, Attribute,
        or Relationship.

        :param iterable elements: The elements to add.
        """
        if not hasattr(elements, "__iter__"):
            elements = [elements]
        for e in elements:
            self._add_single_element(e)

    def rm_elements(self, elements):
        """
        Remove a collection of elements from this data element.
        Each element must be an Atom, Attribute, or Relationship.

        :param iterable elements: The elements to remove.
        """
        if not hasattr(elements, "__iter__"):
            elements = [elements]
        for e in elements:
            self._rm_single_element(e)

    def _add_single_element(self, element):
        """
        Add a single Atom, Attribute, or Relationship to this data element
        if it does not already belong to it.

        :param element: Element to add. Must be of type Atom,
                        Attribute, or Relationship.
        """
        # Maps element types to their containers.
        container_map = {Atom: self._atoms,
                         Attribute: self._attributes,
                         Relationship: self._relationships}
        element_type = type(element)
        if element_type not in [Atom, Attribute, Relationship]:
            raise TypeError(f"Can't add element of type '{element_type}'.")
        container = container_map[element_type]
        if container is None:
            msg = f"{element_type} not implemented for {type(self).__name__}."
            raise AttributeError(msg)

        if element not in container:
            container.add(element)

    def _rm_single_element(self, element):
        """
        Remove a single Atom, Attribute, or Relationship from this
        data element.

        :param element: The element to remove. Must be of type Atom,
                        Attribute, or Relationship.
        """
        # Maps element types to their containers.
        container_map = {Atom: self._atoms,
                         Attribute: self._attributes,
                         Relationship: self._relationships}
        element_type = type(element)
        if element_type not in [Atom, Attribute, Relationship]:
            raise TypeError(f"Unknown element of type '{element_type}'.")
        container = container_map[element_type]
        if container is None:
            msg = f"{element_type} not implemented for {type(self).__name__}."
            raise AttributeError(msg)
        if element not in container:
            msg = f"{element} not found in {self}"
            raise AttributeError(msg)
        container.discard(element)

    def get_atoms(self, atom_name=None, r_type="object"):
        """
        Returns a generator over the atoms of this data element,
        if implemented.

        :param str r_type: How to yield each atom. Possible values
                           are ["object", "dict"]. If "object", yields
                           Atom instances. If "dict", yields dicts from
                           the Atom.to_dict() method.
        :returns: generator over atoms
        :rtype: generator
        """
        if self._atoms is None:
            msg = f"Atoms not implemented for {type(self).__name__}."
            raise AttributeError(msg)
        if r_type.lower() not in ["object", "dict"]:
            raise ValueError("rtype must be 'object' or 'dict'.")
        return_atoms = self._atoms
        if atom_name is not None:
            return_atoms = [a for a in return_atoms if a.term == atom_name]
        for atom in return_atoms:
            if r_type == "object":
                yield atom
            elif r_type == "dict":
                yield atom.to_dict()

    def get_attributes(self, atr_name=None, r_type="object"):
        """
        Returns a generator over the attributes of this data element,
        if implemented.

        :param str atr_name: If not None (default), return only those
                             attributes of type atr_name.
        :param str r_type: How to yield each attribute. Possible values
                           are ["object", "dict"]. If "object", yields
                           Attribute instances. If "dict", yields dicts
                           from the Attribute.to_dict() method.
        :returns: generator over attributes
        :rtype: generator
        """
        if self._attributes is None:
            msg = f"Attributes not implemented for {type(self).__name__}."
            raise AttributeError(msg)
        if r_type.lower() not in ["object", "dict"]:
            raise ValueError("rtype must be 'object' or 'dict'.")
        return_atrs = self._attributes
        if atr_name is not None:
            return_atrs = [a for a in return_atrs if a.atr_name == atr_name]
        for atr in return_atrs:
            if r_type == "object":
                yield atr
            elif r_type == "dict":
                yield atr.to_dict()

    def get_relationships(self, rel_name=None, r_type="object"):
        """
        Returns a generator over the relationships of this concept.

        :param str rel_name: If not None (default), return only those
                             relationships of type rel_name.
        :param str r_type: How to yield each relationship. Possible values
                           are ["object", "dict"]. If "object", yields
                           Relationship instances. If "dict", yields dicts
                           from the Relationship.to_dict() method.
        :returns: generator over relationships
        :rtype: generator
        """
        if r_type.lower() not in ["object", "dict"]:
            raise ValueError("rtype must be 'object' or 'dict'.")
        return_rels = self._relationships
        if rel_name is not None:
            return_rels = [r for r in return_rels if r.rel_name == rel_name]
        for rel in return_rels:
            if r_type == "object":
                yield rel
            elif r_type == "dict":
                yield rel.to_dict()


class Atom(DataElement):
    """
    An Atom is an a unique string, source, source ID, and term type.
    A collection of Atoms is a Concept.

    :param str term: The string of this atom.
    :param str src: The source code of where this atom was found.
    :param str src_id: The ID of this atom in its source.
    :param str term_type: The type of term. E.g. "SY" for synonym.
    :param bool is_preferred: Whether this string is the preferred name
                              in its source.
    :param str ui: The iDISK unique identifier of this atom. Optional.
    """

    _prefix = "DA"

    def __init__(self, term, src, src_id, term_type, is_preferred,
                 ui=None, **attrs):
        super().__init__(ui=ui)
        self.term = term  # 5-HTP
        self.src = src  # NMCD
        self.src_id = src_id  # 1234
        self.term_type = term_type  # SN
        self.is_preferred = is_preferred  # True
        self._attrs = attrs
        self._check_params()
        self._register()

    def __repr__(self):
        # Verbose representation.
        template = "('{}' '{}' '{}' '{}' '{}' '{}')"
        return template.format(self.ui, self.term, self.term_type,
                               self.src, self.src_id, self.is_preferred)

    def __str__(self):
        return f"{self.term}"

    def __hash__(self):
        return hash((self.term.lower(),
                     self.src,
                     self.src_id,
                     self.term_type))

    def __eq__(self, other):
        """
        Test if this atom is equal to other.

        :param Atom other: The atom to test equivalence to.
        """
        if not isinstance(other, Atom):
            return False
        return all([self.term.lower() == other.term.lower(),
                    self.src == other.src,
                    self.src_id == other.src_id,
                    self.term_type == other.term_type,
                    self.attrs == other.attrs])

    def _check_params(self):
        assert isinstance(self.term, str)
        assert isinstance(self.src_id, str)
        assert isinstance(self.is_preferred, bool)
        assert isinstance(self.ui, (type(None), str))
        if SOURCES is not None:
            assert self.src.upper() in SOURCES
        if TERM_TYPES is not None:
            assert self.term_type.upper() in TERM_TYPES

    @property
    def attrs(self):
        return self._attrs

    def to_dict(self):
        """
        Return this atom as a dict. The output format is:

        .. code-block:: json

            {"term": str,
             "src": str,
             "src_id": str,
             "term_type": str,
             "is_preferred": bool,
             **attrs}
        """
        data = {"term": self.term,
                "src": self.src,
                "src_id": self.src_id,
                "term_type": self.term_type,
                "is_preferred": self.is_preferred,
                **self.attrs}
        return data

    @classmethod
    def from_dict(cls, data):
        """
        Create an Atom instance from a JSON string.
        The JSON must be formatted:

        .. code-block:: json

            {"term": str,
             "src": str,
             "src_id": str,
             "term_type": str,
             "is_preferred": bool,
             **attrs}

        :param dict data: The JSON data to load.
        :returns: Atom instance of data.
        :rtype: Atom
        """
        return cls(**data)


class Concept(DataElement):
    """
    An iDISK concept.

    :param str concept_type: The iDISK type of this concept.
                             E.g. "SDSI".
    :param list atoms: List of synonyms for this concept. Each member
                       must be an instance of Atom. Optional.
    :param str ui: the iDISK CUI for this concept. Optional.
    """

    _prefix = "DC"  # The default prefix. Can be changed for each instance.

    def __init__(self, concept_type, atoms=None, ui=None):
        super().__init__(ui=ui)
        self.concept_type = concept_type
        self._preferred_atom = None
        self._atoms = set(atoms) if atoms is not None else set()
        self._attributes = set()
        self._relationships = set()
        self._check_params()
        self._register()

    def __repr__(self):
        return f"{self.preferred_atom} ({self.ui} {self.concept_type})"

    def __str__(self):
        return f"{self.ui}: {self.preferred_atom}"

    def __hash__(self):
        return hash((self.concept_type,
                     tuple(self._atoms)))

    def __eq__(self, other):
        """
        Concept equivalence does not consider attributes or relationships.
        """
        if not isinstance(other, Concept):
            return False
        return all([self.concept_type == other.concept_type,
                    self._atoms == other._atoms])

    def _check_params(self):
        if self._atoms == set():
            raise AssertionError("Concept must have at least one Atom.")
        assert all([isinstance(atom, Atom) for atom in self._atoms])
        assert isinstance(self.concept_type, str)
        assert isinstance(self.ui, (type(None), str))
        if CONCEPT_TYPES is not None:
            assert self.concept_type in CONCEPT_TYPES

    @property
    def preferred_atom(self):
        """
        The preferred term for this concept is the preferred term
        from the highest ranking source. That is, the atom such that
        atom["src"] is the closest to the top of the SOURCES list
        and atom["is_preferred"] is True.

        If SOURCES is not define (e.g. if no config has been loaded)
        then a preferred atom is chosen at random.

        :rtype: Atom
        """
        if self._atoms == []:
            return None
        if self._preferred_atom is None:
            atoms = [atom for atom in self._atoms if atom.is_preferred is True]
            if atoms == []:
                atoms = list(self.get_atoms())

            if SOURCES is None:
                self._preferred_atom = atoms[0]
            else:
                atom_rank = [SOURCES.index(atom.src) for atom in atoms]
                pref = atoms[np.argmin(atom_rank)]
                self._preferred_atom = pref
        return self._preferred_atom

    def to_dict(self):
        """
        Return this concept as an OrderedDict in the iDISK JSON format.

        .. code-block:: json

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

        :returns: Dictionary in the iDISK JSON format.
        :rtype: OrderedDict
        """
        atoms = list(self.get_atoms(r_type="dict"))
        atrs = list(self.get_attributes(r_type="dict"))
        rels = list(self.get_relationships(r_type="dict"))
        d = OrderedDict({"ui": self.ui,
                         "concept_type": self.concept_type,
                         "synonyms": atoms,
                         "attributes": atrs,
                         "relationships": rels})
        return d

    @classmethod
    def from_concept(cls, concept):
        """
        Create a new Concept instance with the same
        Atoms, Attributes, and Relationships as this one.
        Attributes and Relationships are copied and their
        subjects updated.

        :param Concept concept: The concept to copy from.
        :returns: New Concept
        """
        if not isinstance(concept, cls):
            raise TypeError("Argument not of type Concept.")
        new_concept = cls(concept_type=concept.concept_type,
                          atoms=concept._atoms)
        to_add = []
        for atr in concept.get_attributes():
            new_atr = Attribute.from_attribute(atr)
            new_atr.subject = new_concept
            to_add.append(new_atr)
        for rel in concept.get_relationships():
            new_rel = Relationship.from_relationship(rel)
            new_rel.subject = new_concept
            to_add.append(new_rel)
        new_concept.add_elements(to_add)
        new_concept._prefix = concept._prefix
        return new_concept

    @classmethod
    def from_dict(cls, data):
        """
        Creates a concept from a JSON object. The JSON object must have
        the format:

        .. code-block:: json

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

        :param dict data: Input JSON data.
        :returns: Concept instance built from data.
        :rtype: Concept
        """
        atoms = [Atom.from_dict(syn) for syn in data["synonyms"]]
        concept = cls(concept_type=data["concept_type"],
                      atoms=atoms,
                      ui=data["ui"])
        concept.add_elements(atoms)
        atrs = [Attribute.from_dict(atr, subject=concept)
                for atr in data["attributes"]]
        concept.add_elements(atrs)
        # Because we do not have a concept mapping yet, these relationships
        # will have concept UIs as their objects. This can be resolved via
        # Concept.resolve_relationships()
        rels = [Relationship.from_dict(rel, subject=concept)
                for rel in data["relationships"]]
        concept.add_elements(rels)
        return concept

    @classmethod
    def read_jsonl_file(cls, filepath):
        """
        Creates a concept for each line in the JSON lines file.

        :param str filepath: Path to the JSON lines file containing concepts.
        :returns: Generator over Concept instances
        :rtype: generator
        """
        concepts = []
        with open(filepath, 'r') as inF:
            for line in inF:
                concept = Concept.from_dict(json.loads(line))
                concepts.append(concept)
        cls.resolve_relationships()
        return concepts

    @classmethod
    def resolve_relationships(cls):
        """
        When multiple Concept instances are created from a JSON lines file
        and contain relationships that reference each other, we have to wait
        until all concepts are created before the objects of the relationships
        resolved into Relationship instances from their UIs. When this is the
        case, this method should be run after creating all concept instances.
        """
        concepts = cls.get_instances()
        ui2concepts = dict([(c.ui, c) for c in concepts])
        for c in ui2concepts.values():
            for rel in c._relationships:
                if isinstance(rel.object, str):
                    try:
                        obj_concept = ui2concepts[rel.object]
                    except KeyError:
                        msg = f"Object of {rel.rel_name} '{rel.object}' not found"  # noqa
                        logging.warning(msg)
                        continue
                    rel.object = obj_concept


class Attribute(DataElement):
    """
    An attribute of a concept or relationship.

    :param Concept/Relationship subject: The subject of this attribute.
    :param str atr_name: The name of this attribute. E.g. "has_background".
    :param str atr_value: The value of this attribute.
    :param str src: The source code of where this attribute was found.
    """

    _prefix = "DAT"

    def __init__(self, subject, atr_name, atr_value, src, ui=None):
        super().__init__(ui=ui)
        self._increment_counter()
        self.subject = subject
        self.atr_name = atr_name
        self.atr_value = atr_value
        self.src = src
        self._check_params()
        self._register()

    def __repr__(self):
        return self.ui

    def __str__(self):
        return f"{self.subject} *{self.atr_name}* {self.atr_value}"

    def __hash__(self):
        return hash((self.atr_name,
                     self.atr_value,
                     self.src))

    def __eq__(self, other):
        """
        Two Attribute instances are equal if their name, value, and source
        are the same. Their subject is NOT taken into account.

        :param Attribute other: The attribute to compare.
        :rtype: bool
        """
        if not isinstance(other, Attribute):
            return False
        return all([self.atr_name == other.atr_name,
                    self.atr_value == other.atr_value,
                    self.src == other.src])

    def _check_params(self):
        assert isinstance(self.subject, (Concept, Relationship))
        assert isinstance(self.atr_name, str)
        assert isinstance(self.atr_value, (str, numbers.Number))
        assert isinstance(self.src, str)

    def to_dict(self, return_subject=False, verbose_subject=False):
        """
        Output this attribute as a dictionary, optionally with a subject.
        The subject is optional to accord with the iDISK JSON format.

        .. code-block:: json

            {"atr_name": str,
             "atr_value": str,
             "src": str}

        :param bool return_subject: If True, the returned dict contains
                                    a "subject" key.
        :param bool verbose_subject: If True and return_subject is True,
                                     the value of the "subject" key includes
                                     the ui, name, and source, instead of
                                     just the ui.
        :returns: dictionary representation of this attribute.
        :rtype: dict
        """
        atr = OrderedDict({"atr_name": self.atr_name,
                           "atr_value": self.atr_value,
                           "src": self.src})
        if return_subject is True:
            if verbose_subject is True:
                subj = str(self.subject)  # Verbose representation.
            else:
                subj = self.subject.ui
            atr.update({"subject": subj})
            atr.move_to_end("subject", last=False)  # Make subject first
        return atr

    @classmethod
    def from_attribute(cls, attribute):
        new_atr = cls(subject=attribute.subject,
                      atr_name=attribute.atr_name,
                      atr_value=attribute.atr_value,
                      src=attribute.src)
        new_atr._prefix = attribute._prefix
        return new_atr

    @classmethod
    def from_dict(cls, data, subject):
        """
        Create an Attribute instance from data.
        data must be a dict with the following format:

        .. code-block:: json

            {"atr_name": str,
             "atr_value": str,
             "src": str}

        :param dict data: Input dictionary
        :param Concept/Relationship subject: Subject of this attribute.
        :returns: Attribute instance
        :rtype: Attribute
        """
        atr = cls(subject=subject,
                  atr_name=data["atr_name"],
                  atr_value=data["atr_value"],
                  src=data["src"])
        return atr


class Relationship(DataElement):
    """
    A relationship between two concepts.

    :param Concept subject: The subject of this relationship.
    :param str rel_name: The relation. E.g. "ingredient_of".
    :param Concept/str object: The object of this relationship. Can be a
                                    Concept instance or a concept UI.
    :param str src: The source code of where this relationship was found.
    :param list(Attribute) attributes: Any attributes of this relationship.
    """

    _prefix = "DR"

    # TODO: Make sure it's really okay to use 'object' here.
    def __init__(self, subject, rel_name, object, src, ui=None):
        super().__init__(ui=ui)
        self._increment_counter()
        self.subject = subject
        self.rel_name = rel_name
        self.object = object
        self.src = src
        # Relationship attributes
        self._attributes = set()
        self._check_params()
        self._register()

    def __repr__(self):
        return self.ui

    def __str__(self):
        return f"{self.subject} **{self.rel_name}** {self.object}"

    def __hash__(self):
        obj = self.object
        if isinstance(obj, Concept):
            obj = obj.ui
        return hash((self.rel_name,
                     obj,
                     self.src))

    def __eq__(self, other):
        """
        Like Attribute, two Relationship instances are the same if the have
        the same name, object, and source. The subject is NOT considered.
        Equivalence does not consider relationship attributes.

        :param Relationship other: The Relationship to compare.
        :rtype: bool
        """
        if not isinstance(other, Relationship):
            return False
        return all([self.rel_name == other.rel_name,
                    self.object == other.object,
                    self.src == other.src])

    def _check_params(self):
        assert isinstance(self.subject, Concept)
        assert isinstance(self.rel_name, str)
        # Object can be a concept or a concept UI.
        assert isinstance(self.object, (Concept, str))
        if SOURCES is not None:
            assert self.src.upper() in SOURCES

    def to_dict(self, return_subject=False, verbose=False):
        """
        Output this relationship as a dictionary, optionally with a subject.
        The subject is optional to accord with the iDISK JSON format.

        .. code-block:: json

            {"rel_name": str,
             "object": str,
             "src": str,
             "attributes": list}

        :param bool return_subject: If True, the returned dict contains
                                    a "subject" key.
        :param bool verbose_subject: If True and return_subject is True,
                                     the value of the "subject" key includes
                                     the ui, name, and source, instead of
                                     just the ui.
        :returns: dictionary representation of this attribute.
        :rtype: dict
        """
        if verbose is True:
            subj = str(self.subject)
            obj = str(self.object)
        else:
            subj = self.subject.ui
            try:
                obj = self.object.ui
            except AttributeError:  # self.object is a UI, not a Concept.
                obj = self.object

        atrs = list(self.get_attributes(r_type="dict", return_subject=False))
        rel = OrderedDict({"rel_name": self.rel_name,
                           "object": obj,
                           "src": self.src,
                           "attributes": atrs})
        if return_subject is True:
            rel.update({"subject": subj})
            rel.move_to_end("subject", last=False)  # Put the subject first
        return rel

    def get_attributes(self, r_type="object", return_subject=False):
        """
        Return a generator over attributes of this relationship.

        :param r_type str: The type of what to yield. Possible values
                           are ["object", "dict"] If "object", yields
                           Attribute objects. If "dict", yields dicts.

        :param return_subject bool: If True, the returned dict contains
                                    a "subject" key.
        :returns: Generator over attributes
        :rtype: generator
        """
        for atr in self._attributes:
            if r_type == "object":
                yield atr
            elif r_type == "dict":
                yield atr.to_dict(return_subject=return_subject)

    @classmethod
    def from_relationship(cls, relationship):
        new_rel = cls(subject=relationship.subject,
                      rel_name=relationship.rel_name,
                      object=relationship.object,
                      src=relationship.src)
        to_add = []
        for atr in relationship.get_attributes():
            new_atr = Attribute.from_attribute(atr)
            new_atr.subject = new_rel
            to_add.append(new_atr)
        new_rel.add_elements(to_add)
        new_rel._prefix = relationship._prefix
        return new_rel

    @classmethod
    def from_dict(cls, data, subject, concept_mapping=None):
        """
        Create an Relationship instance from data.
        data must be a dict with the following format:

        .. code-block:: json

            {"rel_name": str,
             "object": str,
             "src": str,
             "attributes": [{"atr_name": str,
                             "atr_value": str,
                             "src": str}, {...}]
            }

        :param dict data: Input dictionary
        :param Concept subject: Subject of this relationship.
        :param dict concept_mapping: Mapping from strings to concepts as
                                     {string: Concept}, where string
                                     is equal to data["object"]. Optional.
                                     If None, the object UI is used instead
                                     of a Concept instance.
        :returns: Relationship instance
        :rtype: Relationship
        """
        obj = data["object"]
        if concept_mapping is not None:
            try:
                obj = concept_mapping[data["object"]]
            except KeyError:
                msg = f"object {data['object']} not in concept_mapping"
                raise KeyError(msg)

        rel = cls(subject=subject,
                  rel_name=data["rel_name"],
                  object=obj,
                  src=data["src"])
        atrs = [Attribute.from_dict(atr, subject=rel)
                for atr in data["attributes"]]
        rel.add_elements(atrs)

        return rel
