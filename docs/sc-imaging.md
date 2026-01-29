---
execute_via: python
---

# sc-imaging

<!-- #region -->

Here, you will learn how to structure, featurize, and make a large imaging collection queryable for large-scale machine learning:

1. Load and annotate a {class}`~lamindb.Collection` of microscopy images ([![sc-imaging1/4](https://img.shields.io/badge/imaging1/4-lightgrey)](/sc-imaging))
2. Generate single-cell images ([![sc-imaging2/4](https://img.shields.io/badge/imaging2/4-lightgrey)](/sc-imaging2))
3. Featurize single-cell images ([![sc-imaging3/4](https://img.shields.io/badge/imaging3/4-lightgrey)](/sc-imaging3))
4. Train model to identify autophagy positive cells ([![sc-imaging4/4](https://img.shields.io/badge/imaging4/4-lightgrey)](/sc-imaging4))

```{toctree}
:maxdepth: 1
:hidden:

sc-imaging2
sc-imaging3
sc-imaging4
```

<!-- #endregion -->

First, we load and annotate a collection of microscopy images in TIFF format that [was previously uploaded](https://lamin.ai/scportrait/examples/transform/fl9HcsEgLIr70000).

The images used here were acquired as part of a [study](https://www.biorxiv.org/content/10.1101/2023.06.01.542416v1) on autophagy, a cellular process during which cells recycle their components in autophagosomes.
The study tracked genetic determinants of autophagy through fluorescence microscopy of human U2OS cells.

```python
# pip install 'lamindb[jupyter,bionty]'
!lamin init --storage ./test-sc-imaging --modules bionty
```

```python
import lamindb as ln
import bionty as bt
from tifffile import imread
import matplotlib.pyplot as plt

ln.track()
```

All image metadata is stored in an already ingested `.csv` file on the `scportrait/examples` instance.

```python
metadata_files = (
    ln.Artifact.connect("scportrait/examples")
    .get(key="input_data_imaging_usecase/metadata_files.csv")
    .load()
)

metadata_files.head(2)
```

```python
metadata_files.apply(lambda col: col.unique())
```

## Curating artifacts

<!-- #region -->

All images feature the U2OS cell line, captured using an Opera Phenix microscope at 20X magnification.

To induce autophagy, cells were treated under two conditions:

- Treated: Exposed to `Torin-1` (a starvation-mimicking small molecule) for 14 hours
- Control: Left untreated

The U2OS cells were genetically engineered with fluorescently tagged proteins to visualize the process of autophagosome formation:

- `LC3B` -> Autophagosome marker (visible in mCherry channel)
- `LckLip` -> Membrane-targeted fluorescence protein for cell boundary visualization (visible in Alexa488 channel)
- `Hoechst` -> DNA stain for nucleus identification (visible in DAPI channel)

Each image contains three separate channels:

| Channel | Imaged Structure | Fluorescent Marker  |
| ------- | ---------------- | ------------------- |
| 1       | DNA              | `Hoechst` (DAPI)    |
| 2       | Autophagosomes   | `LC3B` (mCherry)    |
| 3       | Plasma Membrane  | `LckLip` (Alexa488) |

Two genotypes were analyzed:

- WT (Wild-type cells)
- EI24KO (`EI24` gene knockout cells)

For each genotype, two different clonal cell lines were studied, with multiple fields of view (FOVs) captured per experimental condition.

All images are annotated with corresponding metadata to enable efficient querying and analysis.

<!-- #endregion -->

### Define a schema

We define a {class}`~lamindb.Schema` to curate metadata.

```python
ulabel_names = [
    "genotype",
    "stimulation",
    "cell_line_clone",
    "channel",
    "FOV",
    "magnification",
    "microscope",
    "imaged structure",
]

autophagy_imaging_schema = ln.Schema(
    name="Autophagy imaging schema",
    features=[
        *[ln.Feature(name=name, dtype=ln.ULabel.name).save() for name in ulabel_names],
        ln.Feature(name="image_path", dtype=str, description="image path").save(),
        ln.Feature(name="cell_line", dtype=bt.CellLine.name).save(),
        ln.Feature(
            name="resolution", dtype=float, description="conversion factor for px to µm"
        ).save(),
    ],
    coerce_dtype=True,
).save()
```

### Curate the dataset

```python
curator = ln.curators.DataFrameCurator(metadata_files, autophagy_imaging_schema)

try:
    curator.validate()
except ln.core.exceptions.ValidationError as e:
    print(e)
```

Add and standardize missing terms:

```python
curator.cat.standardize("cell_line")

for key in curator.cat.non_validated.keys():
    curator.cat.add_new_from(key)

curator.validate()
```

### Annotate images with metadata

We add images to our `lamindb` instance and annotate them with their metadata.

```python
# Create study feature and associated label
ln.Feature(name="study", dtype=ln.ULabel).save()
ln.ULabel(name="autophagy imaging").save()

artifacts = []

for _, row in metadata_files.iterrows():
    artifact = (
        ln.Artifact.connect("scportrait/examples")
        .filter(key__icontains=row["image_path"])
        .one()
    )
    artifact.save()
    artifact.cell_lines.add(bt.CellLine.filter(name=row.cell_line).one())

    artifact.features.add_values(
        {
            col: row[col]
            for col in [
                "genotype",
                "stimulation",
                "cell_line_clone",
                "channel",
                "FOV",
                "magnification",
                "microscope",
                "resolution",
            ]
        }
        | {"imaged structure": row["imaged structure"], "study": "autophagy imaging"}
    )

    artifacts.append(artifact)
```

```python
artifacts[0].describe()
```

In addition, we create a {class}`~lamindb.Collection` to hold all {class}`~lamindb.Artifact` that belong to this specific imaging study.

```python
collection = ln.Collection(
    artifacts,
    key="Annotated autophagy imaging raw images",
    description="annotated microscopy images of cells stained for autophagy markers",
).save()
```

Let's look at some example images where we match images from the same clone, stimulation condition, and FOV to ensure correct channel alignment.

```python
def plot_example_images(df, n_images=3, title_prefix=""):
    """Plot example images from dataframe."""
    fig, axs = plt.subplots(1, n_images, figsize=(15, 5))
    if n_images == 1:
        axs = [axs]
    for idx, row in df.iterrows():
        path = (
            ln.Artifact.connect("scportrait/examples")
            .get(key=row["image_path"])
            .cache()
        )
        image = imread(path)
        axs[idx].imshow(image)
        axs[idx].set_title(f"{title_prefix}{row['imaged structure']}")
        axs[idx].axis("off")
    return fig, axs


sorted_metadata = metadata_files.sort_values(
    by=["cell_line_clone", "stimulation", "FOV"]
)

# Plot first 3 and last 3
plot_example_images(sorted_metadata.head(3).reset_index(drop=True))
plot_example_images(sorted_metadata.tail(3).reset_index(drop=True));
```

```python
ln.finish()
```
