---
execute_via: python
---

# Hubmap

The [HubMAP (Human BioMolecular Atlas Program) consortium](https://hubmapconsortium.org/) is an initiative mapping human cells to create a comprehensive atlas, with its [Data Portal](https://portal.hubmapconsortium.org/) serving as the platform where researchers can access, visualize, and download tissue data.

Lamin mirrors most of the datasets for simplified access here: [laminlabs/hubmap](https://lamin.ai/laminlabs/hubmap).

If you use the data academically, please cite the original publication [Jain et al. 2023](https://www.nature.com/articles/s41556-023-01194-w).

Here, we show how the HubMAP instance is structured and how datasets and be queried and accessed.
If you'd like to transfer data into your own LaminDB instance, see the [transfer guide](inv:docs#transfer).

```python
# pip install lamindb
!lamin init --modules bionty --storage ./test-hubmap
```

```python
import lamindb as ln
import h5py
import anndata as ad
import pandas as pd
```

Create the central query object for this instance:

```python
db = ln.DB("laminlabs/hubmap")
```

## Getting HubMAP datasets and data products

HubMAP associates several data products, which are the single raw datasets, into higher level datasets.
For example, the dataset [HBM983.LKMP.544](https://portal.hubmapconsortium.org/browse/dataset/20ee458e5ee361717b68ca72caf6044e) has four data products:

1. [raw_expr.h5ad](https://assets.hubmapconsortium.org/f6eb890063d13698feb11d39fa61e45a/raw_expr.h5ad)
1. [expr.h5ad](https://assets.hubmapconsortium.org/f6eb890063d13698feb11d39fa61e45a/expr.h5ad)
1. [secondary_analysis.h5ad](https://assets.hubmapconsortium.org/f6eb890063d13698feb11d39fa61e45a/secondary_analysis.h5ad)
1. [scvelo_annotated.h5ad](https://assets.hubmapconsortium.org/f6eb890063d13698feb11d39fa61e45a/scvelo_annotated.h5ad)

The [laminlabs/hubmap](https://lamin.ai/laminlabs/hubmap) instance registers these data products as {class}`~lamindb.Artifact` that jointly form a {class}`~lamindb.Collection`.

The `key` attribute of `ln.Artifact` and `ln.Collection` corresponds to the IDs of the URLs.
For example, the id in the URL [https://portal.hubmapconsortium.org/browse/dataset/20ee458e5ee361717b68ca72caf6044e](https://portal.hubmapconsortium.org/browse/dataset/20ee458e5ee361717b68ca72caf6044e) is the `key` of the corresponding collection:

```python
small_intenstine_collection = db.Collection.get(key="20ee458e5ee361717b68ca72caf6044e")
small_intenstine_collection
```

We can get all associated data products like:

```python
small_intenstine_collection.artifacts.all().to_dataframe()
```

Note the key of these three `Artifacts` which corresponds to the assets URL.
For example, [https://assets.hubmapconsortium.org/f6eb890063d13698feb11d39fa61e45a/expr.h5ad](https://assets.hubmapconsortium.org/f6eb890063d13698feb11d39fa61e45a/expr.h5ad) is the direct URL to the `expr.h5ad` data product.

Artifacts can be directly loaded:

```python
small_intenstine_artifact = small_intenstine_collection.artifacts.get(
    key__icontains="raw_expr.h5ad"
)
```

<!-- #region -->

```python
adata = small_intenstine_artifact.load()
adata
```

<!-- #endregion -->

## Querying single-cell RNA sequencing datasets

The artifacts corresponding to the `raw_expr.h5ad` data products are labeled with metadata.
The available metadata includes `ln.Reference`, `bt.Tissue`, `bt.Disease`, `bt.ExperimentalFactor`, and many more.
Please have a look at [the instance](https://lamin.ai/laminlabs/hubmap) for more details.

```python
# Get one dataset with a specific type of heart failure
heart_failure_artifact = db.Artifact.filter(
    diseases__name="heart failure with reduced ejection fraction"
).first()
heart_failure_artifact
```

## Querying bulk RNA sequencing datasets

Bulk datasets contain a single file: `expression_matrices.h5`, which is a `hdf5` file containing transcript by sample matrices of TPM and number of reads.
These files are labeled with metadata, including `ln.Reference`, `bt.Tissue`, `bt.Disease`, `bt.ExperimentalFactor`, and many more.
To make the expression data usable with standard analysis workflows, we first read the TPM and raw count matrices from the file and then convert them into a single AnnData object.
In this object, raw read counts are stored in `.X`, and TPM values are added as a separate layer under `.layers["tpm"]`.

<!-- #region -->

```python
# Get one placenta tissue dataset:
placenta_data = db.Artifact.filter(tissues__name="placenta").first().cache()

def load_matrix(group):
    values = group["block0_values"][:]
    columns = group["block0_items"][:].astype(str)
    index = group["axis1"][:].astype(str)

    return pd.DataFrame(values, index=index, columns=columns)


with h5py.File(placenta_data, "r") as f:
    tpm_df = load_matrix(f["tpm"])
    reads_df = load_matrix(f["num_reads"])

# Use raw read counts as the main matrix
placenta_adata = ad.AnnData(X=reads_df.values)
placenta_adata.obs_names = reads_df.index
placenta_adata.var_names = reads_df.columns

# Store TPM normalized values in a layer
placenta_adata.layers["tpm"] = tpm_df.values

placenta_adata
```

<!-- #endregion -->
