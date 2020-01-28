name = "idlib"

import os  # noqa
import json  # noqa
from .schema import Schema  # noqa
from .config import gen_config  # noqa


def load_kb(version_dir):
    version_file = os.path.join(version_dir, ".version")
    version = open(version_file).read().strip()
    version_split = version.split('_')
    kb_version, tags = version_split[0], version_split[1:]
    config_dir = os.path.join(version_dir, "config")
    print(f"Loading iDISK version {version}")
    print(f"  from config at {config_dir}")
    gen_config(config_dir, kb_version)

    concepts_file = os.path.join(version_dir, "concepts/concepts_merged.jsonl")
    kb = read_jsonl_file(concepts_file)
    return kb


def read_jsonl_file(concepts_file):
    from .data_elements import Concept
    concepts = []
    with open(concepts_file, 'r') as inF:
        for line in inF:
            concept = Concept.from_dict(json.loads(line.strip()))
            concepts.append(concept)
    Concept.resolve_relationships()
    return concepts
