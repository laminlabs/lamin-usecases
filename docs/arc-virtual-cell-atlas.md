---
execute_via: python
---

# Arc Virtual Cell Atlas

With 2.5B expression profiles that map on about 600M cells, the [Arc Virtual Cell Atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas) is the globally largest collection of uniformly processed scRNA-seq datasets.
Arc distributes the atlas as 460k parquet and h5ad files on Google Cloud Storage.
Lamin mirrors the atlas here: [laminlabs/arc-virtual-cell-atlas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas).

If you use the data academically, please cite the original publications, [Youngblut _et al._ (2025)](https://arcinstitute.org/manuscripts/scBaseCount) and [Zhang _et al._ (2025)](https://biorxiv.org/10.1101/2025.02.20.639398).

To query atlas with `lamindb`, you have to install it with the GCP (Google Cloud Platform) extra. We also recommend to configure the {mod}`bionty` and {mod}`pertdb` modules.

```python
# pip install 'lamindb[gcp]'
!lamin settings modules set bionty,pertdb
```

Create the central query object for this instance:

```python
import lamindb as ln
import pyarrow.compute as pc

db = ln.DB("laminlabs/arc-virtual-cell-atlas")
```

## Tahoe-100M

Query all artifacts of the `Tahoe-100M` project:

```python
tahoe = db.Project.get(name="Tahoe-100M")
artifacts_tahoe = db.Artifact.filter(projects=tahoe)
artifacts_tahoe.to_dataframe()
```

See the schema and annotations of the first artifact:

```python
artifact1 = artifacts_tahoe[0]
artifact1.describe()
```

<!-- #region -->

You can download an `.h5ad` into your local cache, load it into memory, or open it for streaming:

```python
local_filepath = artifact1.cache()  # sync into cache 
adata = artifact1.load()  # sync into cache and load into memory
with artifact1.open() as adata:  # open for streaming
    ...
```

<!-- #endregion -->

You can query the {class}`~bionty.CellLine` ontology, the {class}`~pertdb.Compound`, and the {class}`~pertdb.CompoundPerturbation` registries via their relationship to {class}`~lamindb.Artifact`. You'll find 50 cell lines:

```python
db.bionty.CellLine.filter(artifacts__in=artifacts_tahoe).to_dataframe(limit=5)
```

380 compounds:

```python
db.pertdb.Compound.filter(artifacts__in=artifacts_tahoe).to_dataframe(limit=5)
```

1,138 perturbations:

```python
db.pertdb.CompoundPerturbation.filter(artifacts__in=artifacts_tahoe).to_dataframe(limit=5)
```

### Query artifacts of interest based on metadata

Let's find which datasets contain A549 cells perturbed with Piroxicam.

```python
a549 = db.bionty.CellLine.filter(name="A549", ontology_id="CVCL_0023")
piroxicam = db.pertdb.Compound.get(name="Piroxicam")

artifacts_a549_piroxicam = artifacts_tahoe.filter(compounds=piroxicam, cell_lines=a549)
artifacts_a549_piroxicam.to_dataframe()
```

### Open the obs metadata parquet file as a PyArrow Dataset

Open the obs metadata file (2.29G) with `PyArrow.Dataset`.

```python
obs_metadata = db.Artifact.filter(
    key__endswith="obs_metadata.parquet", projects=tahoe
).one()
obs_metadata
```

```python
obs_metadata_ds = obs_metadata.open()
obs_metadata_ds.schema
```

Which A549 cells are perturbed with Piroxicam?

<!-- #region -->

```python
filter_expr = (pc.field("cell_name") == a549.name) & (pc.field("drug") == piroxicam.name)
obs_metadata_df = obs_metadata_ds.scanner(filter=filter_expr).to_table().to_pandas()
obs_metadata_df.value_counts("plate")
```

<!-- #endregion -->

<!-- #region -->

Retrieve the corresponding cells from h5ad files.

```python
plate_cells = obs_metadata_df.groupby("plate")["BARCODE_SUB_LIB_ID"].apply(list)

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

This project has 135 collections (27 organisms x 5 count features) for the latest version:

```python
project_scbasecount.collections.filter(version_tag="2026-01-12").to_dataframe()
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
    version_tag="2026-01-12",
    suffix=".h5ad",
    projects=project_scbasecount,
    organisms=organisms.human,
    ulabels=feature_counts.genefull_ex50pas,
    tissues=tissues.brain,
    experimental_factors=efos.single_cell,
).order_by("size").distinct()

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
    version_tag="2026-01-12",
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
