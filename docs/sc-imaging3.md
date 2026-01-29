---
execute_via: python
---

# Featurize single-cell images

Here, we use [scPortrait](https://github.com/MannLabs/scPortrait) to extract features that capture both morphological and intensity-based properties of individual cells:

**Morphological features:**

- Cell area (in pixels)

**Intensity features for each fluorescence channel:**

- Mean intensity
- Median intensity
- 25th and 75th percentile intensities
- Total intensity
- Intensity density (total intensity normalized by area)

These comprehensive cellular profiles enable downstream machine learning analysis to identify cell types and states.

```python
import lamindb as ln
import bionty as bt
import pandas as pd

from scportrait.pipeline.featurization import CellFeaturizer

ln.track()
```

We will use the single-cell image datasets we generated earlier.

```python
# Get single-cell images and config
sc_datasets = (
    ln.Artifact.connect("scportrait/examples")
    .filter(ulabels__name="autophagy imaging", is_latest=True)
    .filter(ulabels__name="scportrait single-cell images")
)

config = (
    ln.Artifact.filter(ulabels__name="autophagy imaging")
    .filter(ulabels__name="scportrait config")
    .distinct()
    .one()
)
```

Extract cellular features from `WT` cells:

```python
# Process single-cell images with scPortrait's featurizer
featurizer = CellFeaturizer(directory=".", config=config.cache(), project_location=None)


def featurize_datasets(artifact_list) -> pd.DataFrame:
    paths = [dataset.cache() for dataset in artifact_list]
    dataset_lookup = {idx: cell.uid for idx, cell in enumerate(artifact_list)}

    results = featurizer.process(
        dataset_paths=paths,
        dataset_labels=list(dataset_lookup.keys()),
        return_results=True,
    )

    # Store original dataset uid for tracking
    results["dataset"] = results["label"].map(dataset_lookup)
    return results.drop(columns=["label"])


# Get WT cells and extract features by condition
wt_cells_afs = sc_datasets.filter(ulabels__name="WT")
class_lookup = {"untreated": 0, "14h Torin-1": 1}

# Get unique conditions
conditions = {af.features.get_values()["stimulation"] for af in wt_cells_afs}
condition_uls = [
    ln.ULabel.connect("scportrait/examples").get(name=name) for name in conditions
]

# Process each condition
features_list = []
for condition_ul in condition_uls:
    cells = wt_cells_afs.filter(ulabels=condition_ul)
    results = featurize_datasets(cells)
    results["class"] = class_lookup[condition_ul.name]
    features_list.append(results)

features = pd.concat(features_list, ignore_index=True)
```

Ingest the generated features to our instance:

```python
artifact = ln.Artifact.from_dataframe(
    features,
    description="featurized single-cell images",
    key="featurization_results/WT.parquet",
).save()

artifact.cell_lines.add(bt.CellLine.get(name="U-2 OS cell"))

artifact.features.add_values(
    {
        "study": "autophagy imaging",
        "genotype": "WT",
    }
)
```

Extract features from `KO` cells using the same approach:

```python
# Process KO cells to see if they behave differently
ko_cells_afs = sc_datasets.filter(ulabels__name="EI24KO")

# Get unique conditions for KO cells
conditions = {af.features.get_values()["stimulation"] for af in ko_cells_afs}
condition_uls = [
    ln.ULabel.connect("scportrait/examples").get(name=name) for name in conditions
]

# Process each condition
features_ko_list = []
for condition_ul in condition_uls:
    cells = ko_cells_afs.filter(ulabels=condition_ul)
    results = featurize_datasets(cells)
    results["class"] = class_lookup[condition_ul.name]
    features_ko_list.append(results)

features_ko = pd.concat(features_ko_list, ignore_index=True)
```

```python
artifact = ln.Artifact.from_dataframe(
    features_ko,
    description="featurized single-cell images",
    key="featurization_results/EI24KO.parquet",
).save()

artifact.cell_lines.add(bt.CellLine.filter(name="U-2 OS cell").one())

artifact.features.add_values(
    {
        "study": "autophagy imaging",
        "genotype": "EI24KO",
    }
)
```

```python
ln.finish()
```
