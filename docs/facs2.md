---
execute_via: python
---

# Append a new dataset

We have one dataset in storage and are about to receive a new dataset.

In this notebook, we'll see how to manage the situation.

```python
import lamindb as ln
import bionty as bt
import readfcs

bt.settings.organism = "human"

ln.track("SmQmhrhigFPL0000")
```

## Ingest a new artifact

### Access ![](https://img.shields.io/badge/Access-10b981)

Let us validate and register another `.fcs` file from [Oetjen18](https://insight.jci.org/articles/view/124928):

```python
filepath = readfcs.datasets.Oetjen18_t1()

adata = readfcs.read(filepath)
# since anndata>=0.12.0, `/` is not allowed in keys
adata.var.index = adata.var.index.str.replace("/", "|")
adata.var["marker"] = adata.var["marker"].str.replace("/", "|")
adata.uns["meta"]["spill"].index = adata.uns["meta"]["spill"].index.str.replace(
    "/", "|"
)
adata.uns["meta"]["spill"].columns = adata.uns["meta"]["spill"].columns.str.replace(
    "/", "|"
)
adata
```

## Transform: normalize ![](https://img.shields.io/badge/Transform-10b981)

```python
import pytometry as pm
```

```python
pm.pp.split_signal(adata, var_key="channel")
```

```python
pm.pp.compensate(adata)
```

```python
pm.tl.normalize_biExp(adata)
```

```python
adata = adata[  # subset to rows that do not have nan values
    adata.to_df().isna().sum(axis=1) == 0
]
```

```python
adata.to_df().describe()
```

### Validate cell markers ![](https://img.shields.io/badge/Validate-10b981)

Let's see how many markers validate:

```python
validated = bt.CellMarker.validate(adata.var.index)
```

Let's standardize and re-validate:

```python
adata.var.index = bt.CellMarker.standardize(adata.var.index)
validated = bt.CellMarker.validate(adata.var.index)
```

Next, register non-validated markers from Bionty:

```python
records = bt.CellMarker.from_values(adata.var.index[~validated])
ln.save(records)
```

Manually create 1 marker:

```python
bt.CellMarker(name="CD14|19").save()
```

Move metadata to obs:

```python
validated = bt.CellMarker.validate(adata.var.index)
adata.obs = adata[:, ~validated].to_df()
adata = adata[:, validated].copy()
```

Now all markers pass validation:

```python
validated = bt.CellMarker.validate(adata.var.index)
assert all(validated)
```

### Register ![](https://img.shields.io/badge/Register-10b981)

```python
schema = ln.Schema.get(name="FACS-AnnData-schema")
curator = ln.curators.AnnDataCurator(adata, schema=schema)
```

```python
artifact = curator.save_artifact(description="Oetjen18_t1")
```

Annotate with more labels:

```python
efs = bt.ExperimentalFactor.lookup()
organism = bt.Organism.lookup()

artifact.labels.add(efs.fluorescence_activated_cell_sorting)
artifact.labels.add(organism.human)
```

```python
artifact.describe()
```

Inspect a PCA fo QC - this collection looks much like noise:

```python
import scanpy as sc

markers = bt.CellMarker.lookup()

sc.pp.pca(adata)
sc.pl.pca(adata, color=markers.cd8.name)
```

## Create a new version of the collection by appending a artifact

Query the old version:

```python
collection_v1 = ln.Collection.get(key="My versioned cytometry collection")
```

```python
collection_v2 = ln.Collection(
    [artifact, collection_v1.ordered_artifacts[0]],
    revises=collection_v1,
    version="2",
)
collection_v2.describe()
```

```python
collection_v2.save()
```
