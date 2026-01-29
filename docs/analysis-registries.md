---
execute_via: python
---

# Cell type annotation and pathway analysis

Please make sure that you run the [GO Ontology](enrichr.ipynb) notebook before this one so that your `CellType` and `Pathway` registries are populated.

```python
!lamin connect use-cases-registries
```

```python
# pip install lamindb celltypist gseapy
import lamindb as ln
import bionty as bt
from lamin_usecases import datasets as ds
import scanpy as sc
import matplotlib.pyplot as plt
import celltypist
import gseapy as gp
```

## An interferon-beta treated dataset

A small peripheral blood mononuclear cell dataset that is split into control and stimulated groups. The stimulated group was treated with interferon beta.
Let's load the dataset and perform some preprocessing:

```python
adata = ds.anndata_seurat_ifnb(preprocess=False, populate_registries=True)
adata
```

```python
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=2000)
sc.pp.pca(adata, n_comps=20)
sc.pp.neighbors(adata, n_pcs=10)
sc.tl.umap(adata)
```

## Analysis: Cell type annotation using CellTypist

```python
model = celltypist.models.Model.load(model="Immune_All_Low.pkl")
```

```python
predictions = celltypist.annotate(
    adata, model="Immune_All_Low.pkl", majority_voting=True
)
adata.obs["cell_type_celltypist"] = predictions.predicted_labels.majority_voting
```

```python
adata.obs["cell_type_celltypist"] = bt.CellType.standardize(
    adata.obs["cell_type_celltypist"]
)
```

```python
sc.pl.umap(
    adata,
    color=["cell_type_celltypist", "stim"],
    frameon=False,
    legend_fontsize=10,
    wspace=0.4,
)
```

## Analysis: Pathway enrichment analysis using Enrichr

This analysis is based on the [GSEApy scRNA-seq Example](https://gseapy.readthedocs.io/en/latest/singlecell_example.html).

First, we compute differentially expressed genes using a Wilcoxon test between stimulated and control cells.

```python
# compute differentially expressed genes
sc.tl.rank_genes_groups(
    adata,
    groupby="stim",
    use_raw=False,
    method="wilcoxon",
    groups=["STIM"],
    reference="CTRL",
)

rank_genes_groups_df = sc.get.rank_genes_groups_df(adata, "STIM")
rank_genes_groups_df.head()
```

Next, we filter out up/down-regulated differentially expressed gene sets:

```python
degs_up = rank_genes_groups_df[
    (rank_genes_groups_df["logfoldchanges"] > 0)
    & (rank_genes_groups_df["pvals_adj"] < 0.05)
]
degs_dw = rank_genes_groups_df[
    (rank_genes_groups_df["logfoldchanges"] < 0)
    & (rank_genes_groups_df["pvals_adj"] < 0.05)
]
degs_up.shape, degs_dw.shape
```

Run pathway enrichment analysis on DEGs and plot top 10 pathways:

```python
enr_up = gp.enrichr(degs_up.names, gene_sets="GO_Biological_Process_2023").res2d
gp.dotplot(enr_up, figsize=(2, 3), title="Up", cmap=plt.cm.autumn_r);
```

```python
enr_dw = gp.enrichr(degs_dw.names, gene_sets="GO_Biological_Process_2023").res2d
gp.dotplot(enr_dw, figsize=(2, 3), title="Down", cmap=plt.cm.winter_r);
```

## Annotate & save dataset

gRegister new features and labels (check out more details [here](./scrna)):

```python
ln.Feature(name="cell_type_celltypist", dtype=bt.CellType).save()
ln.Feature(name="stim", dtype=str).save()
obs_schema = ln.Schema(
    name="celltype_obs_schema",
    features=[
        ln.Feature(name="cell_type_celltypist", dtype=bt.CellType).save(),
        ln.Feature(name="stim", dtype=str).save(),
    ],
).save()
var_schema = ln.Schema(
    name="gene_var_schema",
    itype=bt.Gene,
).save()

schema = ln.Schema(
    name="anndata_seurat_ifnb_schema",
    slots={"obs": obs_schema, "var.T": var_schema},
    otype="AnnData",
).save()
```

Register dataset using an `Artifact` object:

```python
artifact = ln.Artifact.from_anndata(
    adata,
    description="seurat_ifnb_activated_Bcells",
    schema=schema,
).save()
artifact.describe()
```

## Manage pathway objects

Let's create two schemas (two feature sets) for `degs_up` and `degs_dw`:

```python
schema_degs_up = ln.Schema.from_values(
    degs_up.names,
    bt.Gene.symbol,
    name="Up-regulated DEGs STIM vs CTRL",
    organism="human",
).save()
schema_degs_dw = ln.Schema.from_values(
    degs_dw.names,
    bt.Gene.symbol,
    name="Down-regulated DEGs STIM vs CTRL",
    organism="human",
).save()
```

Link the top 10 pathways to the corresponding differentially expressed genes:

```python
def parse_ontology_id_from_enrichr_results(key):
    """Parse out the ontology id.

    "ATF6-mediated Unfolded Protein Response (GO:0036500)" -> ("GO:0036500", "ATF6-mediated Unfolded Protein Response")
    """
    id = key.split(" ")[-1].replace("(", "").replace(")", "")
    name = key.replace(f" ({id})", "")
    return (id, name)


# get ontology ids for the top 10 pathways
enr_up_top10 = [
    pw_id[0]
    for pw_id in enr_up.head(10).Term.apply(parse_ontology_id_from_enrichr_results)
]
enr_dw_top10 = [
    pw_id[0]
    for pw_id in enr_dw.head(10).Term.apply(parse_ontology_id_from_enrichr_results)
]

# get pathway objects
enr_up_top10_pathways = bt.Pathway.from_values(enr_up_top10, bt.Pathway.ontology_id)
enr_dw_top10_pathways = bt.Pathway.from_values(enr_dw_top10, bt.Pathway.ontology_id)
```

Associate the pathways to the differentially expressed genes:

```python
schema_degs_up.pathways.set(enr_up_top10_pathways)
schema_degs_dw.pathways.set(enr_dw_top10_pathways)
schema_degs_up.pathways.to_list("name")
```

With this, we stored the result of the differential expression analysis via schema objects where each schema object links a gene set and its set of enriched pathways in the dataset.

This allows queries along the lines below.

## Query pathways

Querying for pathways contains "interferon-beta" in the name:

```python
bt.Pathway.filter(name__contains="interferon-beta").to_dataframe()
```

Query pathways from a gene:

```python
bt.Pathway.filter(genes__symbol="IFITM1").to_dataframe()
```

Query artifacts from a pathway:

```python
ln.Artifact.filter(feature_sets__pathways__name__icontains="interferon-beta").first()
```

Query schemas from a pathway to learn from which geneset this pathway was computed:

```python
pathway = bt.Pathway.get(ontology_id="GO:0035456")
pathway
```

```python
degs = ln.Schema.get(pathways__ontology_id=pathway.ontology_id)
```

Get the list of genes that are differentially expressed and belong to this pathway:

```python
contributing_genes = pathway.genes.all() & degs.genes.all()
contributing_genes.to_list("symbol")
```

```python
# clean up test instance
!rm -r ./use-cases-registries
!lamin delete --force use-cases-registries
```
