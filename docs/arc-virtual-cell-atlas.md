---
execute_via: python
---

# Arc Virtual Cell Atlas

With 2.5B expression profiles that map to about 600M cells, the Arc Virtual Cell Atlas is the world's largest collection of uniformly processed scRNA-seq datasets.
Arc distributes the atlas as 460k parquet and h5ad files totaling 41TB on Google Cloud Storage, see [github.com/ArcInstitute/arc-virtual-cell-atlas](https://github.com/ArcInstitute/arc-virtual-cell-atlas).
Lamin mirrors the atlas in a database: [lamin.ai/laminlabs/arc-virtual-cell-atlas](https://lamin.ai/laminlabs/arc-virtual-cell-atlas).

If you use the data academically, please cite the original publications, Youngblut _et al._ (2025)[^youngblut25] and Zhang _et al._ (2025).[^zhang25]

To query the atlas with `lamindb`, you have to install it with the GCP (Google Cloud Platform) extra. We also recommend configuring the {mod}`bionty` and {mod}`pertdb` modules.

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

Retrieve the fourteen `.h5ad` datasets of the `Tahoe-100M` project:

```python
tahoe = db.Project.get(name="Tahoe-100M")
artifacts_tahoe = db.Artifact.filter(projects=tahoe, suffix=".h5ad")
artifacts_tahoe.to_dataframe()
```

See the schema and annotations of the first dataset:

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
db.bionty.CellLine.filter(artifacts__in=artifacts_tahoe).distinct().to_dataframe()
```

380 compounds:

```python
db.pertdb.Compound.filter(artifacts__in=artifacts_tahoe).distinct().to_dataframe()
```

1,138 perturbations:

```python
db.pertdb.CompoundPerturbation.filter(artifacts__in=artifacts_tahoe).distinct().to_dataframe()
```

### Query artifacts based on metadata

Let's find which datasets contain A549 cells perturbed with Piroxicam.

```python
a549 = db.bionty.CellLine.get(name="A549")
piro = db.pertdb.Compound.get(name="Piroxicam")

artifacts_a549_piro = artifacts_tahoe.filter(compounds=piro, cell_lines=a549)
artifacts_a549_piro.to_dataframe()
```

### Stream the dataset content

While the artifact metadata tells us which files contain A549 cells and Piroxicam, we use a parquet file to find the exact cells within those files. To this end, we open the metadata file with `pyarrow.Dataset`:

```python
obs_af = db.Artifact.get(key__endswith="obs_metadata.parquet", projects=tahoe)
obs_af.describe()
```

The schema of the parquet file maps to the `pyarrow` schema:

```python
obs_ds = obs_af.open()  # consider using with obs_af.open() as obs_ds
obs_ds.schema
```

<!-- #region -->

:::{admonition} Streaming speed

Streaming large parquet and h5ad files from cloud storage crucially depends on where you run your code. It'll be _much_ faster if you run it in the data center that hosts the data. It'll typically be prohibitively slow if you run it locally. The `gs://arc-institute-virtual-cell-atlas` storage location is accessible from any Google Cloud data center in the US with low latency and no egress fees.

If you want to run logic locally, consider caching datasets prior to opening them for streaming via `.open()`:

```python
local_filepath = obs_af.cache()  # subsequent obs_af.open() will automatically read from the cache
```

:::

Let us now query the columns of interest:

```python
filter_expr = (pc.field("cell_name") == a549.name) & (pc.field("drug") == piro.name)
```

Retrieve the corresponding cells:

```python
plate_cells = obs_df.groupby("plate")["BARCODE_SUB_LIB_ID"].apply(list)
```

And their counts:

```python
adatas = []
for artifact in artifacts_a549_piro:
    plate_name = artifact.features["plate"].name
    idxs = plate_cells.get(plate_name)
    print(f"loading {len(idxs)} cells from plate {plate_name}")
    with artifact.open() as astore:
        adata = astore[idxs].to_memory()  # can also subset genes here
        adatas.append(adata)

# this will print something like this
#> loading 2812 cells from plate plate10
#> ...
# continue with concatenating or other processing of the AnnData objects
```

<!-- #endregion -->

### Train ML models

By applying fast data loaders such as `annbatch`[^gold26] or `scdataset`[^dascenzo25] to locally cached arrays, one can achieve loading times of 50k - 80k vectors/second. This is much faster than cloud-based streaming of the array content.

[Here](https://lamin.ai/laminlabs/arrayloader-benchmarks/artifact/BDttiuV3Te8VB0dU) we zero-copy transferred the `Tahoe-100M` datasets into a database for benchmarking different ML data loaders:

<div style="text-align: center">
<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/D5nJXInD6i3qMItB0002.png" width="700" alt="LaminHub example of lineage-aware syncing of Tahoe-100M datasets" style="padding: 0;">
</div>

[Here](https://lamin.ai/laminlabs/arrayloader-benchmarks/run/ZSuaqX3BWwLzwduW) is an example for a data loading run that loads these `Tahoe-100M` datasets from a pre-shuffled `.zarr` store, obtained as a transformation of the original 14 `.h5ad` files.

## scBaseCount

```python
scbase = db.Project.get(name="scBaseCount")
scbase
```

### Query artifacts based on metadata

An exemplary query:

```python
organisms = db.bionty.Organism.lookup()
tissues = db.bionty.Tissue.lookup()
efos = db.bionty.ExperimentalFactor.lookup()
feature_counts = db.ULabel.filter(type__name="STARsolo count features").lookup()

h5ads_brain = db.Artifact.filter(
    version_tag="2026-01-12",
    suffix=".h5ad",
    projects=scbase,
    organisms=organisms.human,
    ulabels=feature_counts.genefull_ex50pas,
    tissues=tissues.brain,
    experimental_factors=efos.single_cell,
).order_by("size").distinct()

h5ads_brain.to_dataframe()
```

### Cache and load datasets into memory

Load the h5ads as a single `AnnData` by caching the datasets, concatenating them, and loading them into memory:

```python
adata_concat = h5ads_brain[:5].load()
adata_concat
```

Open the sample metadata:

```python
sample_meta = db.Artifact.get(
    version_tag="2026-01-12",
    key__endswith="sample_metadata.parquet",
    projects=scbase,
    organisms=organisms.human,
    ulabels=feature_counts.genefull_ex50pas,
)
sample_meta_dataset = sample_meta.open()
sample_meta_dataset.schema
```

Query the corresponding sample metadata:

```python
filter_expr = pc.field("srx_accession").isin(
    adata_concat.obs["SRX_accession"].astype(str)
)
df = sample_meta_dataset.scanner(filter=filter_expr).to_table().to_pandas()
```

Add the sample metadata to the `AnnData` object:

```python
adata_concat.obs = adata_concat.obs.merge(
    df, left_on="SRX_accession", right_on="srx_accession"
)
adata_concat
```

See the metadata in the `AnnData`:

```python
adata_concat.obs.head()
```

### Explore collections

This project has 135 collections of artifacts (27 organisms x 5 count features) for the latest version:

```python
db.Collection.filter(version_tag="2026-01-12", projects=scbase).to_dataframe()
```

Collections are immutable collections of artifacts, useful for model training or analytical workflows that need to rely on an immutable set rather than a mutable set of artifact that's grouped by a folder or label annotation.

```python tags=["hide-cell"]
assert db.bionty.CellLine.filter(artifacts__in=artifacts_tahoe).distinct().count() == 50
assert db.pertdb.Compound.filter(artifacts__in=artifacts_tahoe).distinct().count() == 380
assert (
    db.pertdb.CompoundPerturbation.filter(artifacts__in=artifacts_tahoe)
    .distinct()
    .count()
    == 1138
)
```

## References

[^youngblut25]: Youngblut ND et al. (2025). scBaseCount: an AI agent-curated, uniformly processed, and continually expanding single cell data repository. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.27.640494).

[^zhang25]: Zhang JQ et al. (2025). Tahoe-100M: A Giga-Scale Single-Cell Perturbation Atlas for Context-Dependent Gene Function and Cellular Modeling. [bioRxiv](https://www.biorxiv.org/content/10.1101/2025.02.20.639398).

[^gold26]: Gold I et al. (2026). MCML - Annbatch Unlocks Terabyte-Scale Training of Biological Data in Anndata. [arXiv](https://arxiv.org/abs/2604.01949).

[^dascenzo25]: D'Ascenzo D & Cultrera di Montesano S (2025). scDataset: Scalable Data Loading for Deep Learning on Large-Scale Single-Cell Omics. [arXiv](https://arxiv.org/abs/2506.01883).
