---
execute_via: python
---

# Bulk RNA-seq

```{note}

More comprehensive examples are provided for these data types:

- {doc}`scrna`
- {doc}`facs`

```

```python
# !pip install 'lamindb[jupyter,bionty]'
!lamin init --storage test-bulkrna --modules bionty
```

```python
import lamindb as ln
import bionty as bt
import pandas as pd
import anndata as ad
from pathlib import Path
```

## Ingest data

### Access ![](https://img.shields.io/badge/Access-10b981)

We start by simulating a [nf-core RNA-seq](https://nf-co.re/rnaseq) run which yields us a count matrix artifact.

(See {doc}`docs:nextflow` for running this with Nextflow.)

```python
# pretend we're running a bulk RNA-seq pipeline
ln.track(
    transform=ln.Transform(key="nf-core RNA-seq", reference="https://nf-co.re/rnaseq")
)
# create a directory for its output
Path("./test-bulkrna/output_dir").mkdir(exist_ok=True)
# get the count matrix
path = ln.core.datasets.file_tsv_rnaseq_nfcore_salmon_merged_gene_counts(
    populate_registries=True
)
# move the count matrix into the output directory
path = path.rename(f"./test-bulkrna/output_dir/{path.name}")
# register the count matrix
ln.Artifact(path, description="Merged Bulk RNA counts").save()
```

### Transform ![](https://img.shields.io/badge/Transform-10b981)

```python
ln.track("s5V0dNMVwL9i0000")
```

Let's query the artifact:

```python
artifact = ln.Artifact.get(description="Merged Bulk RNA counts")
df = artifact.load()
```

If we look at it, we realize it deviates far from the _tidy data_ standard [Wickham14](https://www.jstatsoft.org/article/view/v059i10), conventions of statistics & machine learning [Hastie09](https://link.springer.com/book/10.1007/978-0-387-84858-7), [Murphy12](https://probml.github.io/pml-book/book0.html) and the major Python & R data packages.

Variables are not in columns and observations are not in rows:

```python
df
```

Let's change that and move observations into rows:

```python
df = df.T
df
```

Now, it's clear that the first two rows are in fact no observations, but descriptions of the variables (or features) themselves.

Let's create an AnnData object to model this. First, create a dataframe for the variables:

```python
var = pd.DataFrame({"gene_name": df.loc["gene_name"].values}, index=df.loc["gene_id"])
```

```python
var.head()
```

Now, let's create an AnnData object:

```python
# we're also fixing the datatype here, which was string in the tsv
adata = ad.AnnData(df.iloc[2:].astype("float32"), var=var)
adata
```

The AnnData object is in tidy form and complies with conventions of statistics and machine learning:

```python
adata.to_df()
```

### Curate ![](https://img.shields.io/badge/Curate-10b981)

We define a simple Schema for Bulk RNA datasets that only expects genes with stable IDs to be stored in the dataset.
Later, we can add additional metadata to the curated dataset such as the assay or the organism.

```python
bulk_schema = ln.Schema(itype=bt.Gene.stable_id, otype="AnnData").save()

# set the organism to map to saccharomyces cerevisiae genes
bt.settings.organism = "saccharomyces cerevisiae"

curator = ln.curators.AnnDataCurator(adata, bulk_schema)
curator.validate()
```

Let's create and save the artifact:

```python
curated_af = curator.save_artifact(description="Curated bulk RNA counts")
```

Link additional metadata records:

```python
efs = bt.ExperimentalFactor.lookup()
organism = bt.Organism.lookup()
features = ln.Feature.lookup()
```

```python
curated_af.labels.add(efs.rna_seq, features.assay)
curated_af.labels.add(organism.saccharomyces_cerevisiae, features.organism)
```

```python
curated_af.describe()
```

## Query data

We have two files in the artifact registry:

```python
ln.Artifact.to_dataframe()
```

```python
curated_af.view_lineage()
```

```python
# clean up test instance
!rm -r test-bulkrna
!lamin delete --force test-bulkrna
```
