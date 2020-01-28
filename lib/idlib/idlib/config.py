import os
from configparser import ConfigParser


SOURCES = None
TERM_TYPES = None
CONCEPT_TYPES = None


def gen_config(config_dir, version):
    config_file = os.path.join(config_dir, "kb.ini")
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Config file not found at {config_file}")

    config = ConfigParser()
    config.read(config_file)

    configs = config[version]
    if config.has_option(version, "refer_to"):
        configs = config[configs.get("refer_to")]

    global SOURCES
    global TERM_TYPES
    global CONCEPT_TYPES
    SOURCES = configs.get("sources").split()
    TERM_TYPES = configs.get("term_types").split()
    CONCEPT_TYPES = configs.get("concept_types").split()
