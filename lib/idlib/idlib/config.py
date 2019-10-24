import os
from configparser import ConfigParser


# Search in the current directory,
# any directory specified by the environment variable,
# or in the idlib package.
conf_dir = os.environ.get("CONFIG_DIR")
if conf_dir is None:
    raise EnvironmentError(f"CONFIG_DIR not defined.")
config_file = os.path.join(conf_dir, "kb.ini")
if not os.path.exists(config_file):
    raise FileNotFoundError(f"Config file not found at {config_file}")

kb_version = os.environ.get("PROJECT_VERSION")
if kb_version is None:
    raise EnvironmentError("PROJECT_VERSION not defined.")
# Strip any tags from the version to just get the numbers.
# E.g. 1.0.0_subset -> 1.0.0
kb_version = kb_version.split('_')[0]

CONFIG = ConfigParser()
CONFIG.read(config_file)

configs = CONFIG[kb_version]
if CONFIG.has_option(kb_version, "refer_to"):
    configs = CONFIG[configs.get("refer_to")]

SOURCES = configs.get("sources").split()
TERM_TYPES = configs.get("term_types").split()
CONCEPT_TYPES = configs.get("concept_types").split()
