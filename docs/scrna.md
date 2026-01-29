---
execute_via: python
---

# scRNA-seq

Here, you'll learn how to manage a growing number of scRNA-seq datasets as a single queryable collection:

1. create a dataset (an {class}`~lamindb.Artifact`) and seed a {class}`~lamindb.Collection` (![scrna1/6](https://img.shields.io/badge/scrna1/6-lightgrey))
2. append a new dataset to the collection ([![scrna2/6](https://img.shields.io/badge/scrna2/6-lightgrey)](/scrna2))
3. query & analyze individual datasets ([![scrna3/6](https://img.shields.io/badge/scrna3/6-lightgrey)](/scrna3))
4. load the collection into memory ([![scrna4/6](https://img.shields.io/badge/scrna4/6-lightgrey)](/scrna4))
5. iterate over the collection to train an ML model ([![scrna5/6](https://img.shields.io/badge/scrna5/6-lightgrey)](/scrna-mappedcollection))
6. concatenate the collection to a single `tiledbsoma` array store ([![scrna6/6](https://img.shields.io/badge/scrna6/6-lightgrey)](/scrna-tiledbsoma))

If you're only interested in _using_ a large curated scRNA-seq collection, see the [CELLxGENE guide](inv:docs#cellxgene).

```{toctree}
:maxdepth: 1
:hidden:

scrna2
scrna3
scrna4
scrna-mappedcollection
scrna-tiledbsoma
```

```python
# pip install lamindb
!lamin init --storage ./test-scrna --modules bionty
```

```python
import lamindb as ln
import bionty as bt

ln.track()
```

## Populate metadata registries based on an artifact

Let us look at the standardized data of [Conde _et al._, Science (2022)](https://doi.org/10.1126/science.abl5197), [available from CELLxGENE](https://cellxgene.cziscience.com/collections/62ef75e4-cbea-454e-a0ce-998ec40223d3). {func}`~lamindb.examples.datasets.anndata_human_immune_cells` loads a subsampled version:

```python
adata = ln.core.datasets.anndata_human_immune_cells()
adata
```

To validate & annotate a dataset, we need to define valid features.

```python
ln.Feature(name="donor", dtype=str).save()
ln.Feature(name="tissue", dtype=bt.Tissue).save()
ln.Feature(name="cell_type", dtype=bt.CellType).save()
ln.Feature(name="assay", dtype=bt.ExperimentalFactor).save()
```

Let's attempt saving this dataset as a validated & annotated artifact.

```python
try:
    artifact = ln.Artifact.from_anndata(
        adata, schema="ensembl_gene_ids_and_valid_features_in_obs"
    ).save()
except ln.errors.ValidationError:
    pass
```

One cell type isn't validated because it's not part of the `CellType` registry. Let's create it.

```python
adata.obs["cell_type"] = bt.CellType.standardize(adata.obs["cell_type"])
bt.CellType(name="animal cell").save()
```

We can now save the dataset.

```python
# runs ~10sec because it imports 40k Ensembl gene IDs from a public ontology
artifact = ln.Artifact.from_anndata(
    adata,
    key="datasets/conde22.h5ad",
    schema="ensembl_gene_ids_and_valid_features_in_obs",
).save()
```

Some Ensembl gene IDs don't validate because they stem from an older version of Ensembl. If we wanted to be 100% sure that all gene identifiers are valid Ensembl IDs you can import the genes from an old Ensembl version into the `Gene` registry (see [guide](inv:docs#bio-registries)). One can also enforce this through the `.var.T` schema by setting `schema.maximal_set=True`, which will prohibit any non-valid features in the dataframe.

```python
artifact.describe()
```

## Seed a collection

Let's create a first version of a collection that will encompass many `h5ad` files when more data is ingested.

```{note}

To see the result of the incremental growth, take a look at the [CELLxGENE Census guide](inv:docs#cellxgene) for an instance with ~1k h5ads and ~50 million cells.

```

```python
collection = ln.Collection(artifact, key="scrna/collection1").save()
```

For this version 1 of the collection, collection and artifact match each other. But they're independently tracked and queryable through their registries:

```python
collection.describe()
```

Access the underlying artifacts like so:

```python
collection.artifacts.to_dataframe()
```

See data lineage:

```python
collection.view_lineage()
```

Finish the run and save the notebook.

```python
ln.finish()
```
