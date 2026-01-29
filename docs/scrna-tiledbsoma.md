---
execute_via: python
---

# Concatenate datasets to a single array store

In the previous notebooks, we've seen how to incrementally create a collection of scRNA-seq datasets and train models on it.

Sometimes we want to concatenate all datasets into one big array to speed up ad-hoc queries for slices for arbitrary metadata.

This is also what CELLxGENE does to create Census: a number of `.h5ad` files are concatenated to give rise to a single `tiledbsoma` array store ({doc}`docs:cellxgene`).

```python
import lamindb as ln
import pandas as pd
import scanpy as sc
import tiledbsoma.io
from functools import reduce

ln.track()
```

Query the collection of `h5ad` files that we'd like to concatenate into a single array.

```python
collection = ln.Collection.get(key="scrna/collection1")
collection.describe()
```

## Prepare the AnnData objects

To concatenate the `AnnData` objects into a single `tiledbsoma.Experiment`, they need to have the same `.var` and `.obs` columns.

```python
# load a number of AnnData objects that's small enough to fit into memory
adatas = [artifact.load() for artifact in collection.ordered_artifacts]

# compute the intersection of columns for these objects
var_columns = reduce(
    pd.Index.intersection, [adata.var.columns for adata in adatas]
)  # this only affects metadata columns of features (say, gene annotations)
var_raw_columns = reduce(
    pd.Index.intersection, [adata.raw.var.columns for adata in adatas]
)
obs_columns = reduce(
    pd.Index.intersection, [adata.obs.columns for adata in adatas]
)  # this actually subsets features (dataset dimensions)
```

Prepare the `AnnData` objects for concatenation. Prepare id fields, sanitize `index` names, intersect columns, drop `.obsp`, `.uns` and columns that aren't part of the intersection.

```python
for i, adata in enumerate(adatas):
    del adata.obsp  # not supported by tiledbsoma
    del adata.uns  # not supported by tiledbsoma

    adata.obs = adata.obs.filter(obs_columns)  # filter columns to intersection
    adata.obs["obs_id"] = (
        adata.obs.index
    )  # prepare a column for tiledbsoma to use as an index
    adata.obs["dataset"] = i
    adata.obs.index.name = None

    adata.var = adata.var.filter(var_columns)  # filter columns to intersection
    adata.var["var_id"] = adata.var.index
    adata.var.index.name = None

    drop_raw_var_columns = adata.raw.var.columns.difference(var_raw_columns)
    adata.raw.var.drop(columns=drop_raw_var_columns, inplace=True)
    adata.raw.var["var_id"] = adata.raw.var.index
    adata.raw.var.index.name = None
```

## Create the array store

Save the `AnnData` objects in one array store referenced by an `Artifact`.

```python
soma_artifact = ln.integrations.save_tiledbsoma_experiment(
    adatas,
    description="tiledbsoma experiment",
    measurement_name="RNA",
    obs_id_name="obs_id",
    var_id_name="var_id",
    append_obsm_varm=True,
)
```

:::{note}

Provenance is tracked by writing the current `run.uid` to `tiledbsoma.Experiment.obs` as `lamin_run_uid`.

If you know `tiledbsoma` API, then note that {func}`~docs:lamindb.integrations.save_tiledbsoma_experiment` abstracts over both `tiledbsoma.io.register_anndatas` and `tiledbsoma.io.from_anndata`.

:::

## Query the array store

Here we query the `obs` from the array store.

```python
with soma_artifact.open() as soma_store:
    obs = soma_store["obs"]
    var = soma_store["ms"]["RNA"]["var"]

    obs_columns_store = obs.schema.names
    var_columns_store = var.schema.names

    obs_store_df = obs.read().concat().to_pandas()

    display(obs_store_df)
```

## Append to the array store

Prepare a new `AnnData` object to be appended to the store.

```python
ln.core.datasets.anndata_with_obs().write_h5ad("adata_to_append.h5ad")
```

```python
!lamin save adata_to_append.h5ad --description "adata to append"
```

```python
adata = ln.Artifact.filter(description="adata to append").one().load()

adata.obs_names_make_unique()
adata.var_names_make_unique()

adata.obs["obs_id"] = adata.obs.index
adata.var["var_id"] = adata.var.index

adata.obs["dataset"] = obs_store_df["dataset"].max()

obs_columns_same = [
    obs_col for obs_col in adata.obs.columns if obs_col in obs_columns_store
]
adata.obs = adata.obs[obs_columns_same]

var_columns_same = [
    var_col for var_col in adata.var.columns if var_col in var_columns_store
]
adata.var = adata.var[var_columns_same]

adata.write_h5ad("adata_to_append.h5ad")
```

Append the `AnnData` object from disk by revising `soma_artifact`.

```python
soma_artifact = ln.integrations.save_tiledbsoma_experiment(
    ["adata_to_append.h5ad"],
    revises=soma_artifact,
    measurement_name="RNA",
    obs_id_name="obs_id",
    var_id_name="var_id",
)
```

## Update the array store

Add a new embedding to the existing array store.

```python
# read the data matrix
with soma_artifact.open() as soma_store:
    ms_rna = soma_store["ms"]["RNA"]
    n_obs = len(soma_store["obs"])
    n_var = len(ms_rna["var"])
    X = ms_rna["X"]["data"].read().coos((n_obs, n_var)).concat().to_scipy().tocsr()

# calculate PCA embedding from the queried `X`
pca_array = sc.pp.pca(X, n_comps=2)
```

Open the array store in write mode and add PCA.

```python
with soma_artifact.open(mode="w") as soma_store:
    tiledbsoma.io.add_matrix_to_collection(
        exp=soma_store,
        measurement_name="RNA",
        collection_name="obsm",
        matrix_name="pca",
        matrix_data=pca_array,
    )
```

## See array store mutations

During the append-to and update operations, the data in the array store was changed. LaminDB automatically tracks these revisions recording the number of objects, hashes, and provenance.

```python
soma_artifact.versions.to_dataframe()
```

## View lineage of the array store

Check the generating flow of the array store.

```python
soma_artifact.view_lineage()
```

:::{note}

For the underlying API, see [the tiledbsoma documentation](https://tiledbsoma.readthedocs.io/en/latest/notebooks/tutorial_soma_append_mode.html).

:::
