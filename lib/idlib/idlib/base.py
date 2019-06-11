import re
import weakref
import warnings
import numpy as np
from collections import OrderedDict, defaultdict

from idlib.config import SOURCES, TERM_TYPES, CONCEPT_TYPES


class Atom(object):
    """
    An atom is an instance of a concept with a unique string, source,
    source ID, and term type.

    :param str term: The string of this atom.
    :param str src: The source code of where this atom was found.
    :param str src_id: The ID of this atom in its source.
    :param str term_type: The type of term. E.g. "SY" for synonym.
    :param bool is_preferred: Whether this string is the preferred name
                              in its source.
    :param str ui: The iDISK unique identifier of this atom. Optional.
    """

    _counter = 0
    _ui_template = "DA{0:07}"

    def __init__(self, term, src, src_id, term_type, is_preferred, ui=None):
        self._check_params(term, src, src_id, term_type, is_preferred, ui)
        self.term = term  # 5-HTP
        self.src = src  # NMCD
        self.src_id = src_id  # 1234
        self.term_type = term_type  # SN
        self.is_preferred = is_preferred  # True
        if ui is None:
            self._increment()
            self.ui = self._ui_template.format(self._counter)
        else:
            self.ui = ui
            self.init_counter(int(ui.replace("DA", "")))

    def __repr__(self):
        # Verbose representation.
        template = "('{}' '{}' '{}' '{}' '{}' '{}')"
        return template.format(self.ui, self.term, self.term_type,
                               self.src, self.src_id, self.is_preferred)

    def __str__(self):
        return f"{self.term}"

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
                    self.term_type == other.term_type])

    def _check_params(self, term, src, src_id, term_type, is_preferred, ui):
        assert isinstance(term, str)
        assert src.upper() in SOURCES
        assert isinstance(src_id, str)
        assert term_type.upper() in TERM_TYPES
        if term_type.upper() == "PN":
            msg = "Term type PN (preferred name) is deprecated. Use PT (preferred term) instead."  # noqa
            warnings.warn(msg, DeprecationWarning)
        assert isinstance(is_preferred, bool)
        assert isinstance(ui, (type(None), str))

    def to_dict(self):
        """
        Return this atom as a JSON object. The output format is:

        .. code-block:: json

            {"term": str,
             "src": str,
             "src_id": str,
             "term_type": str,
             "is_preferred": bool}
        """
        data = {"term": self.term,
                "src": self.src,
                "src_id": self.src_id,
                "term_type": self.term_type,
                "is_preferred": self.is_preferred}
        return data

    @classmethod
    def init_counter(cls, num):
        """
        Initialize the unique identifier counter with the given number.

        :param int num: The number to initialize with.
        """
        cls._counter = num

    @classmethod
    def _increment(cls):
        """
        Increment the UI counter by 1.
        """
        cls._counter += 1

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
             "is_preferred": bool}

        :param dict data: The JSON data to load.
        :returns: Atom instance of data.
        :rtype: Atom
        """
        return cls(term=data["term"],
                   src=data["src"],
                   src_id=data["src_id"],
                   term_type=data["term_type"],
                   is_preferred=data["is_preferred"])


class Concept(object):
    """
    An iDISK concept.

    :param str concept_type: The iDISK type of this concept.
                             E.g. "SDSI".
    :param list atoms: List of synonyms for this concept. Each member
                       must be an instance of Atom. Optional.
    :param str ui: the iDISK CUI for this concept. Optional.
    """

    __refs__ = defaultdict(list)  # Holds all instances of this class
    _counter = 0
    _prefix = "DC"  # The default prefix. Can be changed for each instance.
    _ui_template = "{0}{1:07}"  # Prefix, number
    _source_rank = SOURCES

    def __init__(self, concept_type, atoms=[],
                 attributes=[], relationships=[], ui=None):
        self._check_params(concept_type, atoms, attributes,
                           relationships, ui)
        self.concept_type = concept_type
        self.atoms = atoms
        self.attributes = attributes
        self.relationships = relationships
        # Set the UI for this concept
        if ui is None:
            self._increment()
            self.ui = self._ui_template.format(self._prefix, self._counter)
        else:
            self.ui = ui
            self.init_counter(int(ui[-7:]))
        self._preferred_term = None
        self.__refs__[self.__class__].append(weakref.ref(self))

    def __repr__(self):
        return f"{self.preferred_term} ({self.ui} {self.concept_type})"

    def __str__(self):
        return f"{self.ui}: {self.preferred_term}"

    def __eq__(self, other):
        """
        Concept equivalence does not consider attributes or relationships.
        """
        if not isinstance(other, Concept):
            return False
        return all([self.concept_type == other.concept_type,
                    self.atoms == other.atoms])

    def _check_params(self, concept_type, atoms, attributes,
                      relationships, ui):
        assert isinstance(concept_type, str)
        assert concept_type in CONCEPT_TYPES
        assert isinstance(atoms, list)
        assert all([isinstance(atom, Atom) for atom in atoms])
        assert all([isinstance(atr, Attribute) for atr in attributes])
        assert all([isinstance(rel, Relationship) for rel in relationships])
        assert isinstance(ui, (type(None), str))

    @property
    def ui(self):
        """
        The unique identifier is always dynamically determined by the 
        values of self._prefix and self._num.
        """
        return self._ui_template.format(self._prefix, self._num)

    @ui.setter
    def ui(self, value):
        """
        The unique identifier is always dynamically determined by the 
        values of self._prefix and self._num. However, the values of these
        hidden variables can be modified by using the UI setter.

        :param str value: The new unique identifier.
        """
        if not re.match(r'.+[0-9]{7}', value):
            msg = "UI must match the regex '.+[0-9]{7}'. E.g. DC0000001."
            raise ValueError(msg)
        self._num = int(value[-7:])
        self._prefix = value[:-7]

    @property
    def preferred_term(self):
        """
        The preferred term for this concept is the preferred term
        from the highest ranking source. That is, the atom such that
        atom["src"] is the closest to the top of the SOURCES list
        and atom["is_preferred"] is True.
        """
        if self.atoms == []:
            return None
        if self._preferred_term is None:
            atoms = [atom for atom in self.atoms if atom.is_preferred is True]
            atom_rank = [self._source_rank.index(atom.src) for atom in atoms]
            pref = atoms[np.argmin(atom_rank)]
            self._preferred_term = pref
        return self._preferred_term

    def get_atoms(self, r_type="object"):
        """
        Returns a generator over the atoms of this concept.

        :param str r_type: How to yield each atom. Possible values
                           are ["object", "dict"]. If "object", yields
                           Atom instances. If "dict", yields dicts from
                           the Atom.to_dict() method.
        :returns: generator over atoms
        :rtype: generator
        """
        if r_type.lower() not in ["object", "dict"]:
            raise ValueError("rtype must be 'object' or 'dict'.")
        for atom in self.atoms:
            if r_type == "object":
                yield atom
            elif r_type == "dict":
                yield atom.to_dict()

    def get_attributes(self, r_type="object"):
        """
        Returns a generator over the attributes of this concept.

        :param str r_type: How to yield each attribute. Possible values
                           are ["object", "dict"]. If "object", yields
                           Attribute instances. If "dict", yields dicts
                           from the Attribute.to_dict() method.
        :returns: generator over attributes
        :rtype: generator
        """
        if r_type.lower() not in ["object", "dict"]:
            raise ValueError("rtype must be 'object' or 'dict'.")
        for atr in self.attributes:
            if r_type == "object":
                yield atr
            elif r_type == "dict":
                yield atr.to_dict()

    def get_relationships(self, r_type="object"):
        """
        Returns a generator over the relationships of this concept.

        :param str r_type: How to yield each relationship. Possible values
                           are ["object", "dict"]. If "object", yields
                           Relationship instances. If "dict", yields dicts
                           from the Relationship.to_dict() method.
        :returns: generator over relationships
        :rtype: generator
        """
        if r_type.lower() not in ["object", "dict"]:
            raise ValueError("rtype must be 'object' or 'dict'.")
        for rel in self.relationships:
            if r_type == "object":
                yield rel
            elif r_type == "dict":
                yield rel.to_dict()

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
        Set the string to prepend to the UI of each concept.

        :param str prefix: The prefix to set.
        """
        cls._prefix = prefix

    @classmethod
    def _increment(cls):
        """
        Increment the UI counter by 1.
        """
        cls._counter += 1

    @classmethod
    def init_counter(cls, num):
        """
        Initialize the unique identifier counter with the given number.

        :param int num: The number to initialize with.
        """
        cls._counter = num

    @classmethod
    def from_atoms(cls, atoms, concept_type, attributes=[], relationships=[]):
        """
        Create a Concept instance from a collection of Atom instances.

        :param list(Atom) atoms: Atom instances that comprise this concept.
        :param str concept_type: The iDISK type of this concept. E.g. 'SDSI'.
        :param list(Attribute) attributes: Attributes of this concept.
                                           Optional.
        :param list(Relationship) relationships: Relationships of this concept.
                                                 Optional.
        :returns: Concept made up of the specified atoms.
        :rtype: Concept
        """
        assert all([isinstance(atom, Atom) for atom in atoms])
        assert all([isinstance(atr, Attribute) for atr in attributes])
        assert all([isinstance(rel, Relationship) for rel in relationships])
        return cls(concept_type=concept_type,
                   atoms=atoms, attributes=attributes,
                   relationships=relationships)

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
        concept = cls(concept_type=data["concept_type"], ui=data["ui"])
        atoms = [Atom.from_dict(syn) for syn in data["synonyms"]]
        concept.atoms = atoms
        atrs = [Attribute.from_dict(atr, subject=concept)
                for atr in data["attributes"]]
        concept.attributes = atrs
        # Because we do not have a concept mapping yet, these relationships
        # will have concept UIs as their objects. This can be resolved via
        # Concept.resolve_relationships()
        rels = [Relationship.from_dict(rel, subject=concept)
                for rel in data["relationships"]]
        concept.relationships = rels
        return concept

    # TODO: Refactor this to deal with strings that are mapped to multiple
    # concepts. E.g. "aspirin and ibuprofen" |--> "aspirin", "ibuprofen".
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
            for rel in c.relationships:
                if isinstance(rel.object, str):
                    try:
                        obj_concept = ui2concepts[rel.object]
                    except KeyError:
                        msg = f"Relationship object '{rel.object}' not found"
                        warnings.warn(msg)
                        continue
                    rel.object = obj_concept


class Attribute(object):
    """
    An attribute of a concept or relationship.

    :param Concept/Relationship subject: The subject of this attribute.
    :param str atr_name: The name of this attribute. E.g. "has_background".
    :param str atr_value: The value of this attribute.
    :param str src: The source code of where this attribute was found.
    """

    _counter = 0
    _ui_template = "DAT{0:07}"

    def __init__(self, subject, atr_name, atr_value, src):
        self._check_params(subject, atr_name, atr_value, src)
        self._increment()
        self.ui = self._ui_template.format(self._counter)
        self.subject = subject
        self.atr_name = atr_name
        self.atr_value = atr_value
        self.src = src

    def __repr__(self):
        return str(self.to_dict(return_subject=True))

    def __str__(self):
        return f"{self.subject} *{self.atr_name}* {self.atr_value}"

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

    def _check_params(self, subject, atr_name, atr_value, src):
        assert isinstance(subject, (Concept, Relationship))
        assert isinstance(atr_name, str)
        assert isinstance(atr_value, str)
        assert isinstance(src, str)

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
    def _increment(cls):
        """
        Increment the UI counter by 1.
        """
        cls._counter += 1

    @classmethod
    def init_counter(cls, num):
        """
        Initialize the unique identifier counter with the given number.

        :param int num: The number to initialize with.
        """
        cls._counter = num

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


class Relationship(object):
    """
    A relationship between two concepts.

    :param Concept subject: The subject of this relationship.
    :param str rel_name: The relation. E.g. "ingredient_of".
    :param Concept/str obj: The object of this relationship. Can be a
                                    Concept instance or a concept UI.
    :param str src: The source code of where this relationship was found.
    :param list(Attribute) attributes: Any attributes of this relationship.
    """

    _counter = 0
    _ui_template = "DR{0:07}"

    def __init__(self, subject, rel_name, obj, src, attributes=[]):
        self._check_params(subject, rel_name, obj, src, attributes)
        self._increment()
        self.ui = self._ui_template.format(self._counter)
        self.subject = subject
        self.rel_name = rel_name
        self.object = obj
        self.src = src
        # Relationship attributes
        self.attributes = attributes

    def __repr__(self):
        return self.ui

    def __str__(self):
        return f"{self.subject} **{self.rel_name}** {self.object}"

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

    def _check_params(self, subject, rel_name, obj, src, attributes):
        assert isinstance(subject, Concept)
        assert isinstance(rel_name, str)
        # Object can be a concept or a concept UI.
        assert isinstance(obj, (Concept, str))
        assert src.upper() in SOURCES
        for atr in attributes:
            assert isinstance(atr, Attribute)

    def to_dict(self, return_subject=False, verbose=False):
        """
        Output this relationship as a dictionary, optionally with a subject.
        The subject is optional to accord with the iDISK JSON format.

        .. code-block:: json

            {"rel_name": str,
             "object": str,
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
        for atr in self.attributes:
            if r_type == "object":
                yield atr
            elif r_type == "dict":
                yield atr.to_dict(return_subject=return_subject)

    @classmethod
    def init_counter(cls, num):
        """
        Initialize the unique identifier counter with the given number.

        :param int num: The number to initialize with.
        """
        cls._counter = num

    @classmethod
    def _increment(cls):
        """
        Increment the UI counter by 1.
        """
        cls._counter += 1

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
                  obj=obj,
                  src=data["src"])
        atrs = [Attribute.from_dict(atr, subject=rel)
                for atr in data["attributes"]]
        rel.attributes = atrs

        return rel
