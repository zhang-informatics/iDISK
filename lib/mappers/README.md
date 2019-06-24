## Concept Mapping

This package contains classes for calling external concept mapping software such as MetaMap and BioPortal.

### Examples

```python
>>> from mappers import MetaMapDriver
>>> mm = MetaMapDriver("path/to/public_mm/bin")
>>> concepts = mm.map(["1|diabetes", "2|cancer"],
...  		      keep_semtypes={'1': ["dsyn"], '2': ["neop"]})
>>> print(mm.get_best_mappings(concepts)['1']["diabetes"])
{"CandidateMatched": "Diabetes",
 "CandidateCUI": "C0011847",
 "CandidateScore": "-1000",
 ...
}
```
