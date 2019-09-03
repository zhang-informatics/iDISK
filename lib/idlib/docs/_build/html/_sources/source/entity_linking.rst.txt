idlib.entity_linking
====================


Running Entity Linking
----------------------

Entity linking works by following an already created Neo4j knowledge graph schema.

Each external terminology to map to must have an entry in `annotator.ini`.

.. code-block:: na

        foreach concept in input:
          get the node in the schema corresponding to concept.concept_type
          link the concept to the terminology specified by the node.maps_to attribute
          foreach relationship in concept:
            look up the relationship in the schema
            get the node in the schema corresponding to relationship.end_node
            link the relationship.end_node value to the terminology specified by relationship.end_node.maps_to attribute


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
