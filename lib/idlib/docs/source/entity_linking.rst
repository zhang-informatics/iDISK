idlib.entity_linking
====================


Running Entity Linking
----------------------

Entity linking works by following an already created Neo4j knowledge graph schema.
The schema defines which terminologies each concept type will be linked to. These terminologies
are instantiated according to `annotator.ini`.

.. code-block:: bash

        python run_entity_linking.py --concepts_file path/to/concepts.jsonl \
                                     --outfile path/to/outfile.jsonl \
                                     --annotator_conf path/to/annotator.ini \
                                     --uri neo4j_schema_uri \
                                     --user neo4j_username \
                                     --password neo4j password


Linkers
-------

.. autoclass:: idlib.entity_linking.linkers.EntityLinker
    :members:
    :show-inheritance:

.. autoclass:: idlib.entity_linking.MetaMapDriver
    :members:
    :show-inheritance:

.. autoclass:: idlib.entity_linking.QuickUMLSDriver
    :members:
    :show-inheritance:

.. autoclass:: idlib.entity_linking.MedDRARuleBased
    :members:
    :show-inheritance:
