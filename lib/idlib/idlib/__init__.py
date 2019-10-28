name = "idlib"

import os  # noqa
from .schema import Schema  # noqa


def load_environment(version_dir):
    config_file = os.path.join(version_dir, ".config")
    for line in open(config_file, 'r'):
        var, value = line.split('=')
        os.environ[var] = value.strip()

def load_kb(version_dir):
    load_environment(version_dir)
    from idlib.data_elements import Concept
    concepts_file = os.path.join(version_dir, "concepts/concepts_merged.jsonl")
    kb = Concept.read_jsonl_file(concepts_file)
    return kb
