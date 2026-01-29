---
execute_via: python
---

# Flow cytometry

You'll learn how to manage a growing number of flow cytometry datasets as a single queryable collection.

Specifically, you will

1. read a single `.fcs` file as an `AnnData` and seed a versioned collection with it (![facs1/4](https://img.shields.io/badge/facs1/4-lightgrey), current page)
2. append a new dataset (a new `.fcs` file) to create a new version of the collection ([![facs2/4](https://img.shields.io/badge/facs2/4-lightgrey)](facs2))
3. query individual files and cell markers ([![facs3/4](https://img.shields.io/badge/facs3/4-lightgrey)](facs3))
4. analyze the collection and store results as plots ([![facs4/4](https://img.shields.io/badge/facs4/4-lightgrey)](facs4))

```{toctree}
:maxdepth: 1
:hidden:

facs2
facs3
facs4
```

```python
# !pip install 'lamindb[jupyter,bionty]'
!lamin init --storage ./test-facs --modules bionty
```

```python
import lamindb as ln
import bionty as bt
import readfcs

bt.settings.organism = "human"  # globally set organism to human

ln.track("OWuTtS4SApon0000")
```

## Ingest a first artifact

### Access ![](https://img.shields.io/badge/Access-10b981)

We start with a flow cytometry file from [Alpert _et al._, Nat. Med. (2019)](https://pubmed.ncbi.nlm.nih.gov/30842675/).

Calling the following function downloads the artifact and pre-populates a few relevant registries:

```python
ln.core.datasets.file_fcs_alpert19(populate_registries=True)
```

We use [readfcs](https://lamin.ai/docs/readfcs) to read the raw fcs file into memory and create an `AnnData` object:

```python
adata = readfcs.read("Alpert19.fcs")
adata
```

It has the following features:

```python
adata.var.head(10)
```

### Transform: normalize ![](https://img.shields.io/badge/Transform-10b981)

In this use case, we'd like to ingest & store curated data, and hence, we split signal and normalize using the [pytometry](https://github.com/buettnerlab/pytometry) package.

```python
import pytometry as pm
```

First, we'll split the signal from heigh and area metadata:

```python
pm.pp.split_signal(adata, var_key="channel", data_type="cytof")
```

```python
adata
```

Normalize the collection:

```python
pm.tl.normalize_arcsinh(adata, cofactor=150)
```

```{note}

If the collection was a flow collection, you'll also have to compensate the data, if possible. The metadata should contain a compensation matrix, which could then be run by the pytometry compensation function. In the case here, its a cyTOF collection, which doesn't (really) require compensation.

```

### Validate: cell markers ![](https://img.shields.io/badge/Validate-10b981)

First, we validate features in `.var` using {class}`~docs:bionty.CellMarker`:

```python
validated = bt.CellMarker.validate(adata.var.index)
```

We see that many features aren't validated because they're not standardized.

Hence, let's standardize feature names & validate again:

```python
adata.var.index = bt.CellMarker.standardize(adata.var.index)
validated = bt.CellMarker.validate(adata.var.index)
```

The remaining non-validated features don't appear to be cell markers but rather metadata features.

Let's move them into `adata.obs`:

```python
adata.obs = adata[:, ~validated].to_df()
adata = adata[:, validated].copy()
```

Now we have a clean panel of 35 validated cell markers:

```python
validated = bt.CellMarker.validate(adata.var.index)
assert all(validated)  # all markers are validated
```

### Register: metadata ![](https://img.shields.io/badge/Register-10b981)

Next, let's register the metadata features we moved to `.obs`.

For this, we create one feature record for each column in the `.obs` dataframe:

```python
features = ln.Feature.from_dataframe(adata.obs)
ln.save(features)
```

We use the [Experimental Factor Ontology](https://www.ebi.ac.uk/efo/) through Bionty to create a "FACS" label:

```python
bt.ExperimentalFactor.public().search("FACS").head(2)  # search the public ontology
```

We found one for "FACS", let's save it to our in-house registry:

```python
# import the FACS record from the public ontology and save it to the registry
facs = bt.ExperimentalFactor.from_source(ontology_id="EFO:0009108")
facs.save()
```

We don't find one for "CyToF", however, so, let's create it without importing from a public ontology but label it as a child of "is_cytometry_assay":

```python
cytof = bt.ExperimentalFactor(name="CyTOF")
cytof.save()
is_cytometry_assay = bt.ExperimentalFactor(name="is_cytometry_assay")
is_cytometry_assay.save()
cytof.parents.add(is_cytometry_assay)
facs.parents.add(is_cytometry_assay)

is_cytometry_assay.view_parents(with_children=True)
```

Let us look at the content of the registry:

```python
bt.ExperimentalFactor.to_dataframe()
```

### Register: save & annotate with metadata ![](https://img.shields.io/badge/Register-10b981)

```python
var_schema = ln.Schema(
    name="FACS-cell-markers",
    itype=bt.CellMarker,
).save()

obs_schema = ln.Schema(
    name="FACS-sample-metadata",
    itype=ln.Feature,
    flexible=True,
).save()

schema = ln.Schema(
    name="FACS-AnnData-schema",
    otype="AnnData",
    slots={"obs": obs_schema, "var.T": var_schema},
).save()
```

```python
curator = ln.curators.AnnDataCurator(adata, schema=schema)
```

```python
artifact = curator.save_artifact(description="Alpert19")
```

Add more labels:

```python
experimental_factors = bt.ExperimentalFactor.lookup()
organisms = bt.Organism.lookup()

artifact.labels.add(experimental_factors.cytof)
artifact.labels.add(organisms.human)
```

## Inspect the saved artifact

Inspect features on a high level:

```python
artifact.features
```

Inspect low-level features in `.var`:

```python
artifact.features.slots["var.T"].members.to_dataframe().head()
```

Use auto-complete for marker names in the `var` featureset:

```python
markers = artifact.features.slots["var.T"].members.lookup()
markers.cd14
```

In a plot, we can now easily also show gene symbol and Uniprot ID:

```python
import scanpy as sc

sc.pp.pca(adata)
sc.pl.pca(
    adata,
    color=markers.cd14.name,
    title=(
        f"{markers.cd14.name} / {markers.cd14.gene_symbol} /"
        f" {markers.cd14.uniprotkb_id}"
    ),
)
```

## Create a collection from the artifact

```python
ln.Collection(artifact, key="My versioned cytometry collection", version="1").save()
```
