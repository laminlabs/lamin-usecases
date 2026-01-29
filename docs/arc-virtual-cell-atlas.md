---
execute_via: python
---

# Arc Virtual Cell Atlas: scRNA-seq

The [Arc Virtual Cell Atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas) hosts one of the biggest collections of scRNA-seq datasets.

Lamin mirrors the dataset for simplified access here: [laminlabs/arc-virtual-cell-atlas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas).

If you use the data academically, please cite the original publications, [Youngblut _et al._ (2025)](https://arcinstitute.org/manuscripts/scBaseCount) and [Zhang _et al._ (2025)](https://biorxiv.org/10.1101/2025.02.20.639398).

If you'd like to transfer data into your own LaminDB instance, see the [transfer guide](inv:docs#transfer).

```python
# pip install 'lamindb[gcp,bionty,pertdb]'
!lamin init --modules bionty,pertdb --storage ./test-arc-virtual-cell-atlas
```

```python
import lamindb as ln
import pyarrow.compute as pc
import anndata as ad
```

Create the central query object for this instance:

```python
db = ln.DB("laminlabs/arc-virtual-cell-atlas")
```

## Tahoe-100M

```python
project_tahoe = db.Project.get(name="Tahoe-100M")
project_tahoe
```

```python
# one collection in this project
project_tahoe.collections.to_dataframe()
```

Every individual dataset in the atlas is an `.h5ad` file that is registered as an artifact in LaminDB.

Artifact level metadata are registered and can be explored as follows:

```python
# get the collection: https://lamin.ai/laminlabs/arc-virtual-cell-atlas/collection/BpavRL4ntRTzWEE5
collection_tahoe = db.Collection.get(key="tahoe100")
# 14 artifacts in this collection, each correspond to a plate
artifacts_tahoe = collection_tahoe.artifacts.distinct()
artifacts_tahoe.to_dataframe()
```

50 cell lines.

```python
artifacts_tahoe.to_list("cell_lines__name")[:5]
```

380 compounds.

```python
artifacts_tahoe.to_list("compounds__name")[:5]
```

1,138 perturbations.

```python
artifacts_tahoe.to_list("compound_perturbations__name")[:5]
```

```python
# check the curated metadata of the first artifact
artifact1 = artifacts_tahoe[0]
artifact1.describe()
```

16 obs metadata features.

```python
artifact1.features.slots["obs"].members.to_dataframe()
```

### Query artifacts of interest based on metadata

Since all metadata are registered in the sql database, we can explore the datasets without accessing them.

Let's find which datasets contain A549 cells perturbed with Piroxicam.

```python
# lookup objects give you pythonic access to the values
cell_lines = db.bionty.CellLine.lookup("ontology_id")
drugs = db.pertdb.Compound.lookup()

artifacts_a549_piroxicam = artifacts_tahoe.filter(
    cell_lines=cell_lines.cvcl_0023, compounds=drugs.piroxicam
)
artifacts_a549_piroxicam.to_dataframe()
```

<!-- #region -->

You can download an `.h5ad` into your local cache:

```python
artifact1.cache()
```

Or stream it:

```python
artifact1.open()
```

<!-- #endregion -->

### Open the obs metadata parquet file as a PyArrow Dataset

Open the obs metadata file (2.29G) with `PyArrow.Dataset`.

```python
obs_metadata = db.Artifact.filter(
    key__endswith="obs_metadata.parquet", projects=project_tahoe
).one()
obs_metadata
```

```python
obs_metadata_ds = obs_metadata.open()
obs_metadata_ds.schema
```

Which A549 cells are perturbed with Piroxicam.

<!-- #region -->

```python
filter_expr = (pc.field("cell_name") == cell_lines.cvcl_0023.name) & (
    pc.field("drug") == drugs.piroxicam.name
)
obs_metadata_df = obs_metadata_ds.scanner(filter=filter_expr).to_table().to_pandas()
obs_metadata_df.value_counts("plate")
```

<!-- #endregion -->

<!-- #region -->

Retrieve the corresponding cells from h5ad files.

```python
plate_cells = df.groupby("plate")["BARCODE_SUB_LIB_ID"].apply(list)

adatas = []
for artifact in artifacts_a549_piroxicam:
    plate = artifact.features.get_values()["plate"]
    idxs = plate_cells.get(plate)
    print(f"Loading {len(idxs)} cells from plate {plate}")
    with artifact.open() as store:
        adata = store[idxs].to_memory() # can also subst genes here
        adatas.append(adata)
```

<!-- #endregion -->

## scBaseCount

```python
project_scbasecount = db.Project.get(name="scBaseCount")
project_scbasecount
```

This project has 105 collections (21 organisms x 5 count features):

```python
project_scbasecount.collections.to_dataframe()
```

### Query artifacts of interest based on metadata

Often you might not want to access all the h5ads in a collection, but rather filter them by metadata:

```python
organisms = db.bionty.Organism.lookup()
tissues = db.bionty.Tissue.lookup()
efos = db.bionty.ExperimentalFactor.lookup()
feature_counts = db.ULabel.filter(type__name="STARsolo count features").lookup()
```

```python
h5ads_brain = db.Artifact.filter(
    suffix=".h5ad",
    projects=project_scbasecount,
    organisms=organisms.human,
    ulabels=feature_counts.genefull_ex50pas,
    tissues=tissues.brain,
    experimental_factors=efos.single_cell,
).distinct()

h5ads_brain.to_dataframe()
```

### Load the h5ad files with obs metadata

Load the h5ads as a single AnnData:

```python
adata_concat = h5ads_brain[:5].load()
adata_concat
```

Open the sample metadata:

```python
sample_meta = db.Artifact.filter(
    key__endswith="sample_metadata.parquet",
    projects=project_scbasecount,
    organisms=organisms.human,
    ulabels=feature_counts.genefull_ex50pas,
).one()
sample_meta
```

```python
sample_meta_dataset = sample_meta.open()
sample_meta_dataset.schema
```

Fetch corresponding sample metadata:

```python
filter_expr = pc.field("srx_accession").isin(
    adata_concat.obs["SRX_accession"].astype(str)
)
df = sample_meta_dataset.scanner(filter=filter_expr).to_table().to_pandas()
```

Add the sample metadata to the AnnData:

```python
adata_concat.obs = adata_concat.obs.merge(
    df, left_on="SRX_accession", right_on="srx_accession"
)
adata_concat
```

```python
adata_concat.obs.head()
```
