idlib.set_functions
===================

When compiling concepts from multiple sources, it often happens that concepts from different
sources are synonymous. I.e, in iDISK terms, they share one or more atom terms. It is
therefore necessary to merge these concepts. The classes ``Union`` and ``Intersection`` perform
this merging.

It may also be necessary to determine which concepts are singletons. ``Difference`` performs this.


Union
-----

.. currentmodule:: idlib.set_functions
.. autoclass:: idlib.set_functions.Union
    :members:
    :undoc-members:

Intersection
------------

.. autoclass:: idlib.set_functions.Intersection
    :members:
    :undoc-members:
    :show-inheritance:


Difference
----------

.. autoclass:: idlib.set_functions.Difference
    :members:
    :undoc-members:
    :show-inheritance:
