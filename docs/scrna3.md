---
execute_via: python
---

# Query artifacts

Here, we'll query artifacts and inspect their metadata.

This guide can be skipped if you are only interested in how to leverage the overall collection.

```python
import lamindb as ln
import bionty as bt

ln.track("agayZTonayqA")
```

## Query artifacts by provenance metadata

Query the transform, e.g., by `key`:

```python
transform = ln.Transform.get(key="scrna.ipynb")
transform
```

Query the artifact:

```python
ln.Artifact.filter(transform=transform).to_dataframe()
```

## Query artifacts by biological metadata

```python
tissues = bt.Tissue.lookup()

query = ln.Artifact.filter(
    tissues=tissues.blood,
)
query.to_dataframe()
```

## Inspect artifact metadata

Query all artifacts that measured the "cell_type" feature:

```python
query_set = ln.Artifact.filter(feature_sets__features__name="cell_type").all()
artifact1, artifact2 = query_set[0], query_set[1]
```

```python
artifact1.describe()
```

```python
artifact1.view_lineage()
```

```python
artifact2.describe()
```

```python
artifact2.view_lineage()
```
