---
execute_via: python
---

# Query & integrate data

```python
import lamindb as ln
import bionty as bt

ln.track("wukchS8V976U0000")
```

## Inspect the CellMarker registry ![](https://img.shields.io/badge/Access-10b981)

Inspect your aggregated cell marker registry as a `DataFrame`:

```python
bt.CellMarker.to_dataframe().head()
```

Search for a marker (synonyms aware):

```python
bt.CellMarker.search("PD-1").to_dataframe().head(2)
```

Look up markers with auto-complete:

```python
markers = bt.CellMarker.lookup()
markers.cd8
```

## Query artifacts by markers ![](https://img.shields.io/badge/Access-10b981)

Query panels and collections based on markers, e.g., which collections have `'CD8'` in the flow panel:

```python
panels_with_cd8 = ln.Schema.filter(cell_markers=markers.cd8).all()
```

```python
ln.Artifact.filter(feature_sets__in=panels_with_cd8).to_dataframe()
```

Access registries:

```python
features = ln.Feature.lookup()
```

Find shared cell markers between two files:

```python
artifacts = ln.Artifact.filter(feature_sets__in=panels_with_cd8).to_list()
```

```python
shared_markers = (
    artifacts[0].features.slots["var.T"].members
    & artifacts[1].features.slots["var.T"].members
)
shared_markers.to_list("name")
```
