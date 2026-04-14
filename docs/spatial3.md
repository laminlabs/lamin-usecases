---
execute_via: python
---

# Curate and ingest spatial data

Now that we've analyzed and visualized the example dataset in the previous notebooks, let's learn how to curate and ingest our own spatial data.

```python
import lamindb as ln
import bionty as bt
import spatialdata as sd

ln.track()
```

## Creating artifacts

You can use {meth}`~lamindb.Artifact.from_spatialdata` method to create an {class}`~lamindb.Artifact` object from a `SpatialData` object.

```python
example_blobs_sdata = ln.core.datasets.spatialdata_blobs()
example_blobs_sdata
```

```python
blobs_af = ln.Artifact.from_spatialdata(
    example_blobs_sdata, key="example_blobs.zarr"
).save()
blobs_af
```

To retrieve the object back from the database you can, e.g., query by `key`:

```python
example_blobs_sdata = ln.Artifact.get(key="example_blobs.zarr")
local_zarr_path = blobs_af.cache()  # returns a local path to the cached .zarr store
example_blobs_sdata = (
    blobs_af.load()  # calls sd.read_zarr() on a locally cached .zarr store
)
```

To see data lineage:

```python
blobs_af.view_lineage()
```

## Curating artifacts

For the remainder of the guide, we will work with two 10X Xenium and a 10X Visium H&E image datasets that were ingested in raw form [here](https://lamin.ai/laminlabs/lamindata/transform/MN1DpkKGjzbk).

Metadata is stored in two places in the SpatialData object:

1. Dataset level metadata is stored in `sdata.attrs["sample"]`.
2. Measurement specific metadata is stored in the associated tables in `sdata.tables`.

### Define a schema

We define a {class}`lamindb.Schema` to curate both sample and table metadata.

```{dropdown} Curating different spatial technologies
Reading different spatial technologies into SpatialData objects can result in very different objects with different metadata.
Therefore, it can be useful to define technology specific Schemas by reusing Schema components.
```

```python
# define features
ln.Feature(name="organism", dtype=bt.Organism).save()
ln.Feature(name="assay", dtype=bt.ExperimentalFactor).save()
ln.Feature(name="disease", dtype=bt.Disease).save()
ln.Feature(name="tissue", dtype=bt.Tissue).save()
ln.Feature(name="celltype_major", dtype=bt.CellType).save()

# define simple schemas
flexible_metadata_schema = ln.Schema(
    name="Flexible metadata", itype=ln.Feature, coerce_dtype=True
).save()
ensembl_gene_ids = ln.Schema(
    name="Spatial var level (Ensembl gene id)", itype=bt.Gene.ensembl_gene_id
).save()

# define composite schema
spatial_schema = ln.Schema(
    name="Spatialdata schema (flexible)",
    otype="SpatialData",
    slots={
        "attrs:sample": flexible_metadata_schema,
        "tables:table:obs": flexible_metadata_schema,
        "tables:table:var.T": ensembl_gene_ids,
    },
).save()
```

### Curate a Xenium dataset

Create the central query object of our public [lamindata instance](https://lamin.ai/laminlabs/lamindata):

```python
db = ln.DB("laminlabs/lamindata")
```

```python
# load first of two cropped Xenium datasets
xenium_aligned_1_sdata = db.Artifact.get(key="xenium_aligned_1_guide_min.zarr").load()
xenium_aligned_1_sdata
```

```python
xenium_curator = ln.curators.SpatialDataCurator(xenium_aligned_1_sdata, spatial_schema)
try:
    xenium_curator.validate()
except ln.errors.ValidationError as error:
    print(error)
```

```python
xenium_aligned_1_sdata.tables["table"].obs["celltype_major"] = (
    xenium_aligned_1_sdata.tables["table"]
    .obs["celltype_major"]
    .replace(
        {
            "CAFs": "cancer associated fibroblast",
            "Endothelial": "endothelial cell",
            "Myeloid": "myeloid cell",
            "PVL": "perivascular cell",
            "T-cells": "T cell",
            "B-cells": "B cell",
            "Normal Epithelial": "epithelial cell",
            "Plasmablasts": "plasmablast",
            "Cancer Epithelial": "neoplastic epithelial cell",
        }
    )
)
```

```python
try:
    xenium_curator.validate()
except ln.errors.ValidationError as error:
    print(error)
```

```python
xenium_curator.slots["tables:table:obs"].cat.add_new_from("celltype_major")
```

```python
xenium_1_curated_af = xenium_curator.save_artifact(key="xenium1.zarr")
```

```python
xenium_1_curated_af.describe()
```

### Curate additional Xenium datasets

We can reuse the same curator for a second Xenium dataset:

```python
xenium_aligned_2_sdata = db.Artifact.get(key="xenium_aligned_2_guide_min.zarr").load()

xenium_aligned_2_sdata.tables["table"].obs["celltype_major"] = (
    xenium_aligned_2_sdata.tables["table"]
    .obs["celltype_major"]
    .replace(
        {
            "CAFs": "cancer associated fibroblast",
            "Endothelial": "endothelial cell",
            "Myeloid": "myeloid cell",
            "PVL": "perivascular cell",
            "T-cells": "T cell",
            "B-cells": "B cell",
            "Normal Epithelial": "epithelial cell",
            "Plasmablasts": "plasmablast",
            "Cancer Epithelial": "neoplastic epithelial cell",
        }
    )
)
```

```python
xenium_2_curated_af = ln.Artifact.from_spatialdata(
    xenium_aligned_2_sdata, key="xenium2.zarr", schema=spatial_schema
).save()
```

```python
xenium_2_curated_af.describe()
```

### Curate Visium datasets

Analogously, we can define a Schema and Curator for Visium datasets:

```python
visium_aligned_sdata = db.Artifact.get(key="visium_aligned_guide_min.zarr").load()
visium_aligned_sdata
```

```python
visium_curated_af = ln.Artifact.from_spatialdata(
    visium_aligned_sdata, key="visium.zarr", schema=spatial_schema
).save()
```

```python
visium_curated_af.describe()
```

## Overview of the curated datasets

```python
visium_curated_af.view_lineage()
```

```python
ln.Artifact.to_dataframe(features=["assay", "organism", "tissue", "celltype_major"])
```

```python
ln.finish()
```
