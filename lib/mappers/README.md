## Concept Mapping

This package contains classes for calling external concept mapping software such as MetaMap and BioPortal.

### Examples

```python
>>> from mappers import MetaMapDriver
>>> mm = MetaMapDriver("path/to/public_mm/bin")
>>> concepts = mm.map("diabetes", ["dsyn"])
>>> print(mm.get_best_mapping(concepts["diabetes"])
{"CandidateMatched": "Diabetes",
 "CandidateCUI": "C0011847",
 "CandidateScore": "-1000",
 ...
}
```
