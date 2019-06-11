# idlib.set_functions

When compiling concepts from multiple sources, it often happens that concepts from different
sources are synonymous. I.e, in iDISK terms, they share one or more atom terms. It is
therefore necessary to merge these concepts. The classes `Union` and `Intersection` perform
this merging.

It may also be necessary to determine which concepts are singletons. `Difference` performs this.

## Union


#### class idlib.set_functions.Union(concepts, connections=[], run_union=True)
Bases: `object`

An implementation of the union-find datastructure specific for
iDISK Concepts.

The routine starts by finding connections between pairs of concepts
in the input. It then merges the connected concepts, always mergin the
concept with fewer number of atoms into the concept with the greater.

This class can be used to generate a list of candidate connections,
which can then be filtered, by passing `run_union=False` and then
getting the `connections` attribute. Once filtered, they can be passed
back in as the `connections` argument with `run_union=True`.

See the idlib README for example usage.


* **Parameters**

    * **concepts** (*list*) – One or more lists of Concept instances.

    * **connections** (*list*) – A list of int tuples specifying connections
      between pairs of concepts, where each int
      in a given tuple is the index of the concept
      in the concepts argument. Optional. If not
      provided, pairs of concepts are connected if
      they share one or more atom terms.

    * **run_union** (*bool*) – If True (default) run union-find on the input.
      Otherwise, just run find_connections.



#### find_connections()
Finds all pairs of concepts that share one or more atom
terms. Returns connections as a list of int tuples.


* **Returns**

    connections



* **Return type**

    list



#### union_find()
The union-find routine. Given a list of connections, merges them.

## Intersection


#### class idlib.set_functions.Intersection(concepts, connections=[])
Bases: `idlib.set_functions.Union`

The intersection of a list of concepts is the set of all those concepts
that are matched to one or more other concepts.


* **Parameters**

    * **concepts** (*list*) – One or more lists of Concept instances.

    * **connections** (*list*) – A list of int tuples specifying connections
      between pairs of concepts, where each int
      in a given tuple is the index of the concept
      in the concepts argument. Optional. If not
      provided, pairs of concepts are connected if
      they share one or more atom terms.


## Difference


#### class idlib.set_functions.Difference(concepts, connections=[])
Bases: `idlib.set_functions.Union`

The difference of a list of concepts is the set of all those concepts
that could not be matched to at least one other concept.


* **Parameters**

    * **concepts** (*list*) – One or more lists of Concept instances.

    * **connections** (*list*) – A list of int tuples specifying connections
      between pairs of concepts, where each int
      in a given tuple is the index of the concept
      in the concepts argument. Optional. If not
      provided, pairs of concepts are connected if
      they share one or more atom terms.
