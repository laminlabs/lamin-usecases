---
execute_via: python
---

# Multi-modal

Here, we'll showcase how to curate and register ECCITE-seq data from [Papalexi21](https://www.nature.com/articles/s41592-019-0392-0) in the form of [MuData](https://github.com/scverse/mudata) objects.

ECCITE-seq is designed to enable interrogation of single-cell transcriptomes together with surface protein markers in the context of CRISPR screens.

[MuData objects](https://mudata.readthedocs.io) build on top of AnnData objects to store multimodal data.

```python
# pip install lamindb
!lamin init --storage ./test-multimodal --modules bionty
```

```python
import lamindb as ln
import bionty as bt

bt.settings.organism = "human"
ln.track()
```

## Creating MuData Artifacts

lamindb provides a {meth}`~lamindb.Artifact.from_mudata` method to create {class}`~lamindb.Artifact` from MuData objects.

```python
mdata = ln.core.datasets.mudata_papalexi21_subset()
mdata
```

```python
mdata_artifact = ln.Artifact.from_mudata(mdata, key="papalexi.h5mu")
mdata_artifact
```

```python
# MuData Artifacts have the corresponding otype
mdata_artifact.otype
```

```python
# MuData Artifacts can easily be loaded back into memory
papalexi_in_memory = mdata_artifact.load()
papalexi_in_memory
```

## Schema

```python
# define labels
perturbation = ln.ULabel(name="Perturbation", is_type=True).save()
ln.ULabel(name="Perturbed", type=perturbation).save()
ln.ULabel(name="NT", type=perturbation).save()

replicate = ln.ULabel(name="Replicate", is_type=True).save()
ln.ULabel(name="rep1", type=replicate).save()
ln.ULabel(name="rep2", type=replicate).save()
ln.ULabel(name="rep3", type=replicate).save()

# define obs schema
obs_schema = ln.Schema(
    name="mudata_papalexi21_subset_obs_schema",
    features=[
        ln.Feature(name="perturbation", dtype="cat[ULabel[Perturbation]]").save(),
        ln.Feature(name="replicate", dtype="cat[ULabel[Replicate]]").save(),
    ],
).save()

obs_schema_rna = ln.Schema(
    name="mudata_papalexi21_subset_rna_obs_schema",
    features=[
        ln.Feature(name="nCount_RNA", dtype=int).save(),
        ln.Feature(name="nFeature_RNA", dtype=int).save(),
        ln.Feature(name="percent.mito", dtype=float).save(),
    ],
    coerce_dtype=True,
).save()

obs_schema_hto = ln.Schema(
    name="mudata_papalexi21_subset_hto_obs_schema",
    features=[
        ln.Feature(name="nCount_HTO", dtype=int).save(),
        ln.Feature(name="nFeature_HTO", dtype=int).save(),
        ln.Feature(name="technique", dtype=bt.ExperimentalFactor).save(),
    ],
    coerce_dtype=True,
).save()

var_schema_rna = ln.Schema(
    name="mudata_papalexi21_subset_rna_var_schema",
    itype=bt.Gene.symbol,
    dtype=float,
).save()

# define composite schema
mudata_schema = ln.Schema(
    name="mudata_papalexi21_subset_mudata_schema",
    otype="MuData",
    slots={
        "obs": obs_schema,
        "rna:obs": obs_schema_rna,
        "hto:obs": obs_schema_hto,
        "rna:var": var_schema_rna,
    },
).save()
```

```python
mudata_schema.describe()
```

## Validate MuData annotations

```python
curator = ln.curators.MuDataCurator(mdata, mudata_schema)
```

```python
try:
    curator.validate()
except ln.errors.ValidationError:
    pass
```

```python
curator.slots["rna:var"].cat.standardize("columns")
```

```python
curator.slots["rna:var"].cat.add_new_from("columns")
```

```python
curator.validate()
```

## Register curated Artifact

```python
artifact = curator.save_artifact(key="mudata_papalexi21_subset.h5mu")
```

```python
artifact.describe()
```

```python
ln.finish()
```

```python
# clean up test instance
bt.settings.organism = None
!rm -r test-multimodal
!lamin delete --force test-multimodal
```
