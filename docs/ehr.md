---
execute_via: python
---

# EHR

In this guide, we'll look at curating a `DataFrame` storing examplary EHR data, curate it and save it as an annotated `.parquet` file.

1. the dataframe has columns `disease`, `phenotype`, `developmental_stage`, and `age`
2. if columns or values are missing, we standardize the dataframe with default values
3. any values that are present map against specific versions of pre-defined ontologies

```python
# pip install 'lamindb[bionty]'
!lamin init --storage ./test-ehrschema --modules bionty
```

```python
import lamindb as ln
import bionty as bt
import pandas as pd

ln.track("2XEr2IA4n1w4")
```

## Define a schema

Let us first define the ontology versions we want to use.

```python
disease_source = bt.Source.get(
    entity="bionty.Disease", name="mondo", currently_used=True
)

developmental_stage_source = bt.Source.get(
    entity="bionty.DevelopmentalStage", name="hsapdv", currently_used=True
)

bt.Source.filter(entity="bionty.Phenotype", name="pato").update(currently_used=False)
phenotype_source = bt.Source.get(
    entity="bionty.Phenotype", name="hp"
)  # will use add_source
phenotype_source.currently_used = True
phenotype_source.save()
```

Let us now create a schema by defining the features that it measures. The ontology versions are captured via their `uid`.

```python
schema = ln.Schema(
    name="My EHR schema",
    features=[
        ln.Feature(name="age", dtype=int).save(),
        ln.Feature(
            name="disease",
            dtype=bt.Disease,
            default_value="normal",
            nullable=False,
            cat_filters={"source__uid": disease_source.uid},
        ).save(),
        ln.Feature(
            name="developmental_stage",
            dtype=bt.DevelopmentalStage,
            default_value="unknown",
            nullable=False,
            cat_filters={"source__uid": developmental_stage_source.uid},
        ).save(),
        ln.Feature(
            name="phenotype",
            dtype=bt.Phenotype,
            default_value="unknown",
            nullable=False,
            cat_filters={"source__uid": phenotype_source.uid},
        ).save(),
    ],
).save()
# look at a dataframe of the features that are part of the schema
schema.features.to_dataframe()
```

## Curate an example dataset

Create an example `DataFrame` that has all required columns but one is misnamed.

```python
dataset = {
    "disease": pd.Categorical(
        [
            "Alzheimer disease",
            "diabetes mellitus",
            pd.NA,
            "Hypertension",
            "asthma",
        ]
    ),
    "phenotype": pd.Categorical(
        [
            "Mental deterioration",
            "Hyperglycemia",
            "Tumor growth",
            "Increased blood pressure",
            "Airway inflammation",
        ]
    ),
    "developmental_stage": pd.Categorical(
        ["Adult", "Adult", "Adult", "Adult", "Child"]
    ),
    "patient_age": [70, 55, 60, 65, 12],
}
df = pd.DataFrame(dataset)
df
```

Let's validate it.

```python
curator = ln.curators.DataFrameCurator(df, schema)
try:
    curator.validate()
except ln.errors.ValidationError as e:
    assert "column 'age' not in dataframe" in str(e)
    print(e)
```

Fix the name of the `patient_age` column to be `age`.

```python
df.columns = df.columns.str.replace("patient_age", "age")
try:
    curator.validate()
except ln.errors.ValidationError as e:
    assert "non-nullable series 'disease' contains null values" in str(e)
    print(e)
```

Standardize the dataframe so that the missing value gets populated with the default value.

```python
curator.standardize()
try:
    curator.validate()
except ln.errors.ValidationError as e:
    print(e)
    # assert "2 terms are not validated: 'Tumor growth', 'Airway inflammation'" in str(e)
```

Add the 'normal' term to the disease registry.

```python
bt.Disease(name="normal", description="Healthy condition").save()
```

Curate the remaining mismatches manually.

```python
diseases = bt.Disease.public().lookup()
phenotypes = bt.Phenotype.public().lookup()
developmental_stages = bt.DevelopmentalStage.public().lookup()

df["disease"] = df["disease"].cat.rename_categories(
    {"Hypertension": diseases.hypertensive_disorder.name}
)
df["phenotype"] = df["phenotype"].cat.rename_categories(
    {
        "Tumor growth": phenotypes.neoplasm.name,
        "Airway inflammation": phenotypes.bronchitis.name,
    }
)
df["developmental_stage"] = df["developmental_stage"].cat.rename_categories(
    {
        "Adult": developmental_stages.adolescent_stage.name,
        "Child": developmental_stages.child_stage.name,
    }
)

curator.validate()
```

```python
!rm -rf test-ehrschema
!lamin delete --force test-ehrschema
```
