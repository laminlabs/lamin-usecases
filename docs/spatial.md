---
execute_via: python
---

# Spatial RNA-seq

<!-- #region -->

Here, you'll learn how to manage spatial datasets:

1. query & analyze spatial datasets (![spatial1/4](https://img.shields.io/badge/spatial1/4-lightgrey))
2. create and share interactive visualizations with vitessce ([![spatial2/4](https://img.shields.io/badge/spatial2/4-lightgrey)](/spatial2))
3. curate and ingest spatial data (![spatial3/4](https://img.shields.io/badge/spatial3/4-lightgrey))
4. load the collection into memory & train a ML model ([![spatial3/4](https://img.shields.io/badge/spatial4/4-lightgrey)](/spatial3))

```{toctree}
:maxdepth: 1
:hidden:

spatial2
spatial3
spatial4
```

<!-- #endregion -->

Spatial omics data integrates molecular profiling (e.g., transcriptomics, proteomics) with spatial information, preserving the spatial organization of cells and tissues.
It enables high-resolution mapping of molecular activity within biological contexts, crucial for understanding cellular interactions and microenvironments.

Many different spatial technologies such as multiplexed imaging, spatial transcriptomics, spatial proteomics, whole slide imaging, spatial metabolomics, and 3D tissue reconstruction exist which can all be stored in the [SpatialData](https://github.com/scverse/spatialdata) data framework.
For more details we refer to the original publication:

Marconato, L., Palla, G., Yamauchi, K.A. et al. SpatialData: an open and universal data framework for spatial omics. Nat Methods 22, 58–62 (2025). [https://doi.org/10.1038/s41592-024-02212-x](https://doi.org/10.1038/s41592-024-02212-x)

```{note}
A collection of curated spatial datasets in SpatialData format is available on the [scverse/spatialdata-db instance](https://lamin.ai/scverse/spatialdata-db).
```

```{dropdown} spatial data vs SpatialData terminology
When we mention spatial data, we refer to data from spatial assays, such as spatial transcriptomics or proteomics, that includes spatial coordinates to represent the organization of molecular features in tissue.
When we refer SpatialData, we mean spatial omics data stored in the scverse SpatialData framework.
```

# Query and analyze spatial data

```python
# pip install lamindb spatialdata spatialdata-plot squidpy
!lamin init --storage ./test-spatial --modules bionty
```

```python
import warnings

warnings.filterwarnings("ignore")

import lamindb as ln
import scanpy as sc
import spatialdata as sd
import spatialdata_plot as pl
import squidpy as sq
from matplotlib import pyplot as plt

ln.track()
```

## Query by biological metadata

We'll work with a human lung cancer dataset generated using 10x Genomics Xenium platform and available in a public instance.
This FFPE (formalin-fixed paraffin-embedded) tissue sample includes spatial gene expression profiles.

Create the central query object of our public [lamindata instance](https://lamin.ai/laminlabs/lamindata):

```python
db = ln.DB("laminlabs/lamindata")
```

Now query the database to find Xenium datasets from lung tissue:

```python
all_xenium_data = db.Artifact.filter(
    assay="Xenium Spatial Gene Expression", tissue="lung"
)

all_xenium_data.to_dataframe()
```

## Analyze spatial data

```python
sdata = all_xenium_data[0].load()
```

Spatial data datasets stored as SpatialData objects can easily be examined and analyzed through the SpatialData framework, [squidpy](https://github.com/scverse/squidpy), and [scanpy](https://github.com/scverse/scanpy).

We use [spatialdata-plot](https://github.com/scverse/spatialdata-plot) to get an overview of the dataset:

```python
axes = plt.subplots(1, 2, figsize=(10, 10))[1].flatten()
sdata.pl.render_images("he_image", scale="scale4").pl.show(
    ax=axes[0], title="H&E image"
)
sdata.pl.render_images("morphology_focus", scale="scale4").pl.show(
    ax=axes[1], title="Morphology image"
)
```

We can visualize the segmentations masks by rendering the shapes from the SpatialData object:

```python
def crop0(x):
    return sd.bounding_box_query(
        x,
        min_coordinate=[20000, 7000],
        max_coordinate=[22000, 7500],
        axes=("x", "y"),
        target_coordinate_system="global",
    )


crop0(sdata).pl.render_images("he_image", scale="scale2").pl.render_shapes(
    "cell_boundaries", fill_alpha=0, outline_alpha=0.5
).pl.show(
    figsize=(10, 5), title="H&E image & cell boundaries", coordinate_systems="global"
)
```

For any Xenium analysis we would use the `AnnData` object, which contains the count matrix, cell and gene annotations.
It is stored in the `spatialdata.tables` slot:

```python
adata = sdata.tables["table"]
adata
```

```python
adata.obs
```

Quality control metrics can be calculated using `scanpy.pp.calculate_qc_metrics`.
Cells and genes can be filtered based on minimum thresholds using `scanpy.pp.filter_cells` and `scanpy.pp.filter_genes`.

For normalization and dimensionality reduction, standard [scanpy](https://github.com/scverse/scanpy) workflows include:

- `scanpy.pp.normalize_total` for library size normalization
- `scanpy.pp.log1p` for log transformation
- `scanpy.pp.pca` for principal component analysis
- `scanpy.pp.neighbors` for neighborhood graph computation

For this analysis, we use precomputed Leiden clustering results rather than running the full preprocessing pipeline.
For a full tutorial on how to perform analysis of Xenium data, we refer to [squidpy's Xenium tutorial](https://squidpy.readthedocs.io/en/stable/notebooks/tutorials/tutorial_xenium.html).

Visualize annotation on UMAP and spatial coordinates:

```python
sc.pl.umap(
    adata,
    color=[
        "total_counts",
        "n_genes_by_counts",
        "leiden",
    ],
    wspace=0.1,
)
```

```python
sq.pl.spatial_scatter(
    adata,
    library_id="spatial",
    shape=None,
    color=[
        "leiden",
    ],
)
```

```python
ln.finish()
```
