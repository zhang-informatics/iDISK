import os
from configparser import ConfigParser


# Read configuration
idlib_dir = os.path.dirname(__file__)
config_file = os.path.join(idlib_dir, "idisk.ini")
if os.path.exists(config_file) is False:
    raise FileNotFoundError(f"Config file '{config_file}' not found.")
CONFIG = ConfigParser()
CONFIG.read(config_file)

SOURCES = CONFIG["base"].get("sources").split()
TERM_TYPES = CONFIG["base"].get("term_types").split()
CONCEPT_TYPES = CONFIG["base"].get("concept_types").split()
