---
execute_via: python
---

# Standardize and append a dataset

Here, we'll learn

- how to standardize a less well curated dataset
- how to append it to the growing versioned collection

```python
import lamindb as ln
import bionty as bt

ln.track()
```

Let's now consider a less-well curated dataset:

```python
adata = ln.core.datasets.anndata_pbmc68k_reduced()
# we don't trust the cell type annotation in this dataset
adata.obs.rename(columns={"cell_type": "cell_type_untrusted"}, inplace=True)
# this is our dataset
adata
```

We can't save it in validated form.

```python
try:
    ln.Artifact.from_anndata(
        adata,
        key="scrna/dataset2.h5ad",
        schema="ensembl_gene_ids_and_valid_features_in_obs",
    ).save()
except SystemExit as e:
    print("Error captured:", e)
```

Let's convert Gene symbols to Ensembl ids via {meth}`~docs:lamindb.models.CanCurate.standardize`. Note that this is a non-unique mapping and the first match is kept because the `keep` parameter in `.standardize()` defaults to `"first"`:

```python
adata.var["ensembl_gene_id"] = bt.Gene.standardize(
    adata.var.index,
    field=bt.Gene.symbol,
    return_field=bt.Gene.ensembl_gene_id,
    organism="human",
)
# use ensembl_gene_id as the index
adata.var.index.name = "symbol"
adata.var = adata.var.reset_index().set_index("ensembl_gene_id")
```

None of the cell type names are valid.

```python
adata.obs["cell_type_untrusted"].unique()
```

Let's look up the non-validated cell types using the values of the public ontology and create a mapping.

```python
cell_types = bt.CellType.public().lookup()
name_mapping = {
    "Dendritic cells": cell_types.dendritic_cell.name,
    "CD19+ B": cell_types.b_cell_cd19_positive.name,
    "CD4+/CD45RO+ Memory": cell_types.effector_memory_cd45ra_positive_alpha_beta_t_cell_terminally_differentiated.name,
    "CD8+ Cytotoxic T": cell_types.cd8_positive_alpha_beta_cytotoxic_t_cell.name,
    "CD4+/CD25 T Reg": cell_types.cd4_positive_cd25_positive_alpha_beta_regulatory_t_cell.name,
    "CD14+ Monocytes": cell_types.cd14_positive_monocyte.name,
    "CD56+ NK": cell_types.cd56_positive_cd161_positive_immature_natural_killer_cell_human.name,
    "CD8+/CD45RA+ Naive Cytotoxic": cell_types.cd8_positive_alpha_beta_memory_t_cell_cd45ro_positive.name,
    "CD34+": cell_types.cd34_positive_cd56_positive_cd117_positive_common_innate_lymphoid_precursor_human.name,
    "CD38-positive naive B cell": cell_types.cytotoxic_t_cell.name,
}
```

And standardize cell type names using this name mapping:

```python
adata.obs["cell_type"] = adata.obs["cell_type_untrusted"].map(name_mapping)
adata.obs["cell_type"].unique()
```

Define the corresponding feature:

```python
ln.Feature(name="cell_type", dtype=bt.CellType).save()
```

Save the artifact with cell type and gene annotations:

```python
artifact_trusted = ln.Artifact.from_anndata(
    adata,
    key="scrna/dataset2.h5ad",
    description="10x reference adata, trusted cell type annotation",
    schema="ensembl_gene_ids_and_valid_features_in_obs",
).save()
artifact_trusted.describe()
```

Query the previous collection:

```python
collection_v1 = ln.Collection.get(key="scrna/collection1")
```

Create a new version of the collection by sharding it across the new `artifact` and the artifact underlying version 1 of the collection:

```python
collection_v2 = collection_v1.append(artifact_trusted).save()
```

See data lineage.

```python
collection_v2.view_lineage()
```
