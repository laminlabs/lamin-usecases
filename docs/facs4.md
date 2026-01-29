---
execute_via: python
---

# Analyze the collection and save a result

```python
import lamindb as ln
import bionty as bt

ln.track("zzJzdgJ763Dy0000")
```

```python
ln.Collection.to_dataframe()
```

```python
collection = ln.Collection.get(key="My versioned cytometry collection", version="2")
```

```python
adata = collection.load(join="inner")
```

The `AnnData` has the reference to the individual files in the `.obs` annotations:

```python
adata.obs.artifact_uid.cat.categories
```

By default, the intersection of features is used:

```python
adata.var.index
```

Let us create a plot:

```python
markers = bt.CellMarker.lookup()
```

```python
import scanpy as sc

sc.pp.pca(adata)
sc.pl.pca(adata, color=markers.cd8.name, save="_cd8")
```

```python
artifact = ln.Artifact("./figures/pca_cd8.pdf", description="My result on CD8").save()
artifact.view_lineage()
```

Given the image is part of the notebook, there isn't an actual need to save it and you can also rely on the report that you'll create when saving the notebook:

```
ln.finish()
```

```python
# clean up test instance
!rm -r test-flow
!lamin delete --force test-facs
```
