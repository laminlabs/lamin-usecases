---
execute_via: python
---

# Train a spatial ML model

Here, we show how we can query, access, and combine several SpatialData datasets across different technologies to train a Dense Net which predicts cell types Xenium data from an associated H&E image.
Specifically, we use the H&E image from Visium data, and the cell type information from overlapping Xenium data.
Both modalities are spatially aligned via an affine transformation.

This tutorial is adapted from the [SpatialData documentation](https://spatialdata.scverse.org/en/stable/tutorials/notebooks/notebooks/examples/densenet.html).

```python
import warnings

warnings.filterwarnings("ignore")

import lamindb as ln
import numpy as np

import spatialdata as sd
from spatialdata import transform
from spatialdata.dataloader.datasets import ImageTilesDataset

import pytorch_lightning as pl
from pytorch_lightning.callbacks import LearningRateMonitor
from pytorch_lightning.callbacks.progress import TQDMProgressBar

import torch.multiprocessing as mp

mp.set_start_method("spawn", force=True)

ln.track()
```

First, we query for Xenium and Visium datasets that we curated and ingested on the [previous page](https://docs.lamin.ai/spatial3):

```python
xenium_af = ln.Artifact.filter(
    tissue="breast",
    assay="10x Xenium",
).first()
```

```python
visium_af = ln.Artifact.filter(
    tissue="breast",
    assay="Visium Spatial Gene Expression",
).first()
```

From the query results, we load the SpatialData datasets:

```python
xenium_sd = xenium_af.load()
visium_sd = visium_af.load()
```

Because both datasets were curated with matching tissue, disease, and organism metadata, we can merge them for multi-modal analysis.

```python
merged_sd = sd.SpatialData(
    images={
        "CytAssist_FFPE_Human_Breast_Cancer_full_image": visium_sd.images[
            "CytAssist_FFPE_Human_Breast_Cancer_full_image"
        ],
    },
    shapes={
        "cell_circles": xenium_sd.shapes["cell_circles"],
        "cell_boundaries": xenium_sd.shapes["cell_boundaries"],
    },
    tables={"table": xenium_sd["table"]},
)
```

The Visium image is rotated with respect to the Xenium data.

<img src="https://spatialdata.scverse.org/en/stable/_images/dense_net_cell_types.png" width="600" height="500" alt="Dense network of cell types">

Next, we create an `ImageTilesDataset` using our merged `SpatialData` object.
We further import an image tile transform, the corresponding Pytorch Lightning `DataModule`, and the final `DenseNet` model from an existing script.

````{dropdown} Code of tile_transform, ImageTilesDataset and the DenseNetModel
```{eval-rst}
.. literalinclude:: spatial_ml.py
   :language: python
   :caption: Spatial cell type classification model definition
```
````

```python
from spatial_ml import tile_transform, TilesDataModule, DenseNetModel

dataset = ImageTilesDataset(
    sdata=merged_sd,
    regions_to_images={"cell_circles": "CytAssist_FFPE_Human_Breast_Cancer_full_image"},
    regions_to_coordinate_systems={"cell_circles": "aligned"},
    table_name="table",
    tile_dim_in_units=6
    * np.mean(
        transform(merged_sd["cell_circles"], to_coordinate_system="aligned").radius
    ),
    transform=tile_transform,
    rasterize=True,
    rasterize_kwargs={"target_width": 32},
)
```

Now, we only need to set up a DataModule, our model, and we can start training.

```python
pl.seed_everything(7)

tiles_data_module = TilesDataModule(batch_size=64, num_workers=8, dataset=dataset)

tiles_data_module.setup()
train_dl = tiles_data_module.train_dataloader()
val_dl = tiles_data_module.val_dataloader()
test_dl = tiles_data_module.test_dataloader()

model = DenseNetModel(
    learning_rate=1e-5,
    in_channels=dataset[0][0].shape[0],
    num_classes=len(merged_sd["table"].obs["celltype_major"].cat.categories.tolist()),
)

trainer = pl.Trainer(
    max_epochs=1,
    callbacks=[
        LearningRateMonitor(logging_interval="step"),
        TQDMProgressBar(refresh_rate=5),
    ],
    log_every_n_steps=20,
)
```

```python
trainer.fit(model, datamodule=tiles_data_module)
trainer.test(model, datamodule=tiles_data_module)
```

If we were to perform a prediction and evaluate it like outlined in the [original guide](https://spatialdata.scverse.org/en/stable/tutorials/notebooks/notebooks/examples/densenet.html), we would see predictions like:

<!-- #region -->
<img src="https://spatialdata.scverse.org/en/stable/_images/dense_net_predicted.png" width="1000" height="450" alt="Model predictions">
<!-- #endregion -->

```python
ln.finish()
```

```python
# clean up test instance
!rm -rf test-spatial
!lamin delete --force test-spatial
```
