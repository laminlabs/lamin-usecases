---
execute_via: python
---

# Analyze a collection in memory

Here, we'll analyze the growing collection by loading it into memory.
This is only possible if it's not too large.
If your data is large, you'll likely want to iterate over the collection to train a model, the topic of the next page ([![scrna5/6](https://img.shields.io/badge/scrna5/6-lightgrey)](/scrna-mappedcollection)).

```python
import lamindb as ln
import bionty as bt

ln.track()
```

```python
collection = ln.Collection.get(key="scrna/collection1")
```

```python
collection.artifacts.to_dataframe()
```

If the collection isn't too large, we can now load it into memory.

Under-the-hood, the `AnnData` objects are concatenated during loading.

The amount of time this takes depends on a variety of factors.

If it occurs often, one might consider storing a concatenated version of the collection, rather than the individual pieces.

```python
adata = collection.load()
```

The default is an outer join during concatenation as in pandas:

```python
adata
```

The `AnnData` has the reference to the individual artifacts in the `.obs` annotations:

```python
adata.obs.artifact_uid.cat.categories
```

We can easily obtain ensemble IDs for gene symbols using the look up object:

```python
genes = bt.Gene.lookup(field="symbol")
```

```python
genes.itm2b.ensembl_gene_id
```

Let us create a plot:

```python
import scanpy as sc

sc.pp.pca(adata, n_comps=2)
```

```python
pca_itm2b_fig = sc.pl.pca(
    adata,
    color=genes.itm2b.ensembl_gene_id,
    title=(
        f"{genes.itm2b.symbol} / {genes.itm2b.ensembl_gene_id} /"
        f" {genes.itm2b.description}"
    ),
    return_fig=True
)
pca_itm2b_fig.figure.savefig('pca_itm2b.pdf')
```

We could save a plot as a pdf and then see it in the flow diagram:

```python
artifact = ln.Artifact(
    "pca_itm2b.pdf", description="My result on ITM2B"
).save()
artifact.view_lineage()
```

But given the image is part of the notebook, we can also rely on the report that we create when saving the notebook:

```
ln.finish()
```
