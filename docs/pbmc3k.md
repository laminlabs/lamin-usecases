# Preprocessing and clustering 3k PBMCs (legacy workflow)


```python
import lamindb as ln
import bionty as bt
```


```python
project = ln.Project(
    name="pbmc3k"
).save()
ln.track(project=project)
```

    [92m→[0m returning project with same name: 'pbmc3k'
    [92m→[0m loaded Transform('vRS5s14AcZzc0002', key='clustering-2017.ipynb'), re-started Run('7U2tk6fwPXuNsJYt') at 2026-04-17 17:30:17 UTC
    [92m→[0m notebook imports: lamindb-core==2.3.1 matplotlib==3.10.8 pandas==2.3.3 scanpy==1.12.1
    [94m•[0m recommendation: to identify the notebook across renames, pass the uid: ln.track("vRS5s14AcZzc", project="pbmc3k")



```python
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import scanpy as sc
```

This notebook has been adapted from a [tutorial](https://scanpy.readthedocs.io/en/stable/tutorials/basics/clustering-2017.html) in the scanpy documentation, with additional changes showing how Lamin can be used. 

The data consist of *3k PBMCs from a Healthy Donor* and are freely available from 10x Genomics ([here](http://cf.10xgenomics.com/samples/cell-exp/1.1.0/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz) from this [webpage](https://support.10xgenomics.com/single-cell-gene-expression/datasets/1.1.0/pbmc3k)). On a unix system, you can uncomment and run the following to download and unpack the data. The last line creates a directory for writing processed data.


```bash
%%bash
mkdir -p data
cd data
test -f pbmc3k_filtered_gene_bc_matrices.tar.gz || curl https://cf.10xgenomics.com/samples/cell/pbmc3k/pbmc3k_filtered_gene_bc_matrices.tar.gz -o pbmc3k_filtered_gene_bc_matrices.tar.gz
tar -xzf pbmc3k_filtered_gene_bc_matrices.tar.gz
```

Read in the count matrix into an AnnData object, which holds many slots for annotations and different representations of the data. It also comes with its own HDF5-based file format: `.h5ad`.


```python
adata = sc.read_10x_mtx(
    "data/filtered_gene_bc_matrices/hg19/",  # the directory with the `.mtx` file
    var_names="gene_symbols",  # use gene symbols for the variable names (variables-axis index)
    cache=True,  # write a cache file for faster subsequent reading
)
```


```python
adata.var_names_make_unique()  # this is unnecessary if using `var_names='gene_ids'` in `sc.read_10x_mtx`
```


```python
adata
```




    AnnData object with n_obs × n_vars = 2700 × 32738
        var: 'gene_ids'



### Save the AnnData object with the raw/unprocessed 3k PBMCs in Lamin


```python
ln.Artifact.from_anndata(adata, key="raw_pbmc3k.h5ad").save()
```

    ... uploading Qz0NISO5dWCWCRiq0000.h5ad: 100.0%





    Artifact(uid='Qz0NISO5dWCWCRiq0000', key='raw_pbmc3k.h5ad', description=None, suffix='.h5ad', kind='dataset', otype='AnnData', size=21594848, hash='lxBNr0B2HeQRe8PI7PIhuw', n_files=None, n_observations=2700, branch_id=1, created_on_id=1, space_id=1, storage_id=2, run_id=6325, schema_id=None, created_by_id=46, created_at=2026-04-17 17:35:10 UTC, is_locked=False, version_tag=None, is_latest=True)




```python
ln.finish()
```

    [94m•[0m please hit CTRL + s to save the notebook in your editor .. [92m✓[0m
    [93m![0m cells [(3, 6), (6, 4), (4, 4), (9, 42), (42, 9), (46, None), (None, 48)] were not run consecutively
    [92m→[0m finished Run('SKG5QPKhkdzwGIxN') after 57s at 2026-04-17 14:08:12 UTC
    [92m→[0m go to: https://lamin.ai/laminlabs/lamindata/transform/vRS5s14AcZzc0001
    [92m→[0m to update your notebook from the CLI, run: lamin save /home/sg/Projects/pbmc3kclustering/clustering-2017.ipynb


## Preprocessing

### Load the Anndata object with the raw/unprocessed 3k PBMCs from Lamin


```python
adata = ln.Artifact.get(key="raw_pbmc3k.h5ad").load()
```

    ... synchronizing raw_pbmc3k.h5ad: 100.0%


Show those genes that yield the highest fraction of counts in each single cell, across all cells.


```python
sc.pl.highest_expr_genes(adata, n_top=20)
```


    
![png](clustering-2017_files/clustering-2017_17_0.png)
    


Basic filtering:


```python
sc.pp.filter_cells(adata, min_genes=200)  # this does nothing, in this specific case
sc.pp.filter_genes(adata, min_cells=3)
adata
```




    AnnData object with n_obs × n_vars = 2700 × 13714
        obs: 'n_genes'
        var: 'gene_ids', 'n_cells'



Let's assemble some information about mitochondrial genes, which are important for quality control.

With `pp.calculate_qc_metrics`, we can compute many metrics very efficiently.


```python
# annotate the group of mitochondrial genes as "mt"
adata.var["mt"] = adata.var_names.str.startswith("MT-")
sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)
```

A violin plot of some of the computed quality measures:

* the number of genes expressed in the count matrix
* the total counts per cell
* the percentage of counts in mitochondrial genes


```python
sc.pl.violin(
    adata,
    ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
    jitter=0.4,
    multi_panel=True,
)
```


    
![png](clustering-2017_files/clustering-2017_24_0.png)
    


Remove cells that have too many mitochondrial genes expressed or too many total counts:


```python
fig, axs = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
sc.pl.scatter(adata, x="total_counts", y="pct_counts_mt", show=False, ax=axs[0])
sc.pl.scatter(adata, x="total_counts", y="n_genes_by_counts", show=False, ax=axs[1]);
```


    
![png](clustering-2017_files/clustering-2017_26_0.png)
    


Actually do the filtering by slicing the `AnnData` object.


```python
adata = adata[
    (adata.obs.n_genes_by_counts < 2500) & (adata.obs.n_genes_by_counts > 200) & (adata.obs.pct_counts_mt < 5),
    :,
].copy()
adata.layers["counts"] = adata.X.copy()
```


```python
adata
```




    AnnData object with n_obs × n_vars = 2638 × 13714
        obs: 'n_genes', 'n_genes_by_counts', 'total_counts', 'total_counts_mt', 'pct_counts_mt'
        var: 'gene_ids', 'n_cells', 'mt', 'n_cells_by_counts', 'mean_counts', 'pct_dropout_by_counts', 'total_counts'
        layers: 'counts'



Total-count normalize (library-size correct) the data matrix $\mathbf{X}$ to 10,000 reads per cell, so that counts become comparable among cells.


```python
sc.pp.normalize_total(adata, target_sum=1e4)
```

Logarithmize the data:


```python
sc.pp.log1p(adata)
```

Identify highly-variable genes.


```python
sc.pp.highly_variable_genes(
    adata,
    layer="counts",
    n_top_genes=2000,
    min_mean=0.0125,
    max_mean=3,
    min_disp=0.5,
    flavor="seurat_v3",
)
```


```python
sc.pl.highly_variable_genes(adata)
```


    
![png](clustering-2017_files/clustering-2017_36_0.png)
    


Scale each gene to unit variance. Clip values exceeding standard deviation 10.


```python
adata.layers["scaled"] = adata.X.toarray()
sc.pp.scale(adata, max_value=10, layer="scaled")
```

## Principal component analysis

Reduce the dimensionality of the data by running principal component analysis (PCA), which reveals the main axes of variation and denoises the data.


```python
sc.pp.pca(adata, layer="scaled", svd_solver="arpack")
```

We can make a scatter plot in the PCA coordinates, but we will not use that later on.


```python
sc.pl.pca(adata, annotate_var_explained=True, color="CST3")
```


    
![png](clustering-2017_files/clustering-2017_43_0.png)
    


Let us inspect the contribution of single PCs to the total variance in the data. This gives us information about how many PCs we should consider in order to compute the neighborhood relations of cells, e.g. used in the clustering function  `sc.tl.louvain()` or tSNE `sc.tl.tsne()`. In our experience, often a rough estimate of the number of PCs does fine.


```python
sc.pl.pca_variance_ratio(adata, n_pcs=20)
```


    
![png](clustering-2017_files/clustering-2017_45_0.png)
    


## Computing the neighborhood graph


```python
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)
```

## Embedding the neighborhood graph


```python
sc.tl.umap(adata)
```


```python
sc.pl.umap(adata, color=["CST3", "NKG7", "PPBP"])
```


    
![png](clustering-2017_files/clustering-2017_50_0.png)
    


As we set the `.X` attribute of `adata` to be the normalized data, the previous plots showed the normalized gene expression.
You can also plot the counts directly, or the "scaled_hvg" (normalized, logarithmized, and scaled) data.


```python
sc.pl.umap(adata, color=["CST3", "NKG7", "PPBP"], layer="counts")
```


    
![png](clustering-2017_files/clustering-2017_52_0.png)
    



```python
sc.pl.umap(adata, color=["CST3", "NKG7", "PPBP"], layer="scaled")
```


    
![png](clustering-2017_files/clustering-2017_53_0.png)
    


## Clustering the neighborhood graph


```python
sc.tl.leiden(
    adata,
    resolution=0.7,
    random_state=0,
    flavor="igraph",
    n_iterations=2,
    directed=False,
)
adata.obs["leiden"] = adata.obs["leiden"].copy()
adata.uns["leiden"] = adata.uns["leiden"].copy()
adata.obsm["X_umap"] = adata.obsm["X_umap"].copy()
```


```python
sc.pl.umap(adata, color=["leiden", "CD14", "NKG7"])
```


    
![png](clustering-2017_files/clustering-2017_56_0.png)
    


## Finding marker genes

Let us compute a ranking for the highly differential genes in each cluster.


```python
sc.tl.rank_genes_groups(adata, "leiden", mask_var="highly_variable", method="wilcoxon")
sc.pl.rank_genes_groups(adata, n_genes=25, sharey=False)
```

    ranking genes
        finished (0:00:00)



    
![png](clustering-2017_files/clustering-2017_59_1.png)
    


Most of these genes are found in the highly expressed genes with notable exceptions like `CD8A` (see the below dotplot).

Leiden Group | Markers | Cell Type
---|---|---
0 | IL7R | CD4 T cells
1 | CD14, LYZ | CD14+ Monocytes
2 | MS4A1 |	B cells
3 | CD8A |	CD8 T cells
4 | GNLY, NKG7 | 	NK cells
5 | FCGR3A, MS4A7 |	FCGR3A+ Monocytes
6 | FCER1A, CST3 |	Dendritic Cells
7 | PPBP |	Megakaryocytes

Let us also define a list of marker genes for later reference.


```python
marker_genes = [
    *["IL7R", "CD79A", "MS4A1", "CD8A", "CD8B", "LYZ", "CD14"],
    *["LGALS3", "S100A8", "GNLY", "NKG7", "KLRB1"],
    *["FCGR3A", "MS4A7", "FCER1A", "CST3", "PPBP"],
]
```

Actually mark the cell types.


```python
new_cluster_names = [
    "CD4 T",
    "B",
    "CD14+ Monocytes",
    "NK",
    "CD8 T",
    "FCGR3A+ Monocytes",
    "Dendritic",
    "Megakaryocytes",
]
adata.rename_categories("leiden", new_cluster_names)
adata.obs['cell_type']=adata.obs['leiden']
```


```python
sc.pl.umap(adata, color="cell_type", legend_loc="on data", title="", frameon=False)
```


    
![png](clustering-2017_files/clustering-2017_65_0.png)
    


Now that we annotated the cell types, let us visualize the marker genes.


```python
sc.pl.dotplot(adata, marker_genes, groupby="cell_type")
```


    
![png](clustering-2017_files/clustering-2017_67_0.png)
    


### Save the resulting AnnData object in Lamin

During the course of this analysis, the AnnData accumlated the following annotations.


```python
adata
```




    AnnData object with n_obs × n_vars = 2638 × 13714
        obs: 'n_genes', 'n_genes_by_counts', 'total_counts', 'total_counts_mt', 'pct_counts_mt', 'leiden', 'cell_type'
        var: 'gene_ids', 'n_cells', 'mt', 'n_cells_by_counts', 'mean_counts', 'pct_dropout_by_counts', 'total_counts', 'highly_variable', 'highly_variable_rank', 'means', 'variances', 'variances_norm', 'mean', 'std'
        uns: 'hvg', 'leiden', 'leiden_colors', 'log1p', 'neighbors', 'pca', 'rank_genes_groups', 'umap', 'cell_type_colors'
        obsm: 'X_pca', 'X_umap'
        varm: 'PCs'
        layers: 'counts', 'scaled'
        obsp: 'connectivities', 'distances'




```python
ln.Artifact.from_anndata(adata, key="result_pbmc3k.h5ad").save()
```

    [92m→[0m creating new artifact version for key 'result_pbmc3k.h5ad' in storage 's3://lamindata'
    ... uploading w2SjnZkk8KyqJMjR0002.h5ad: 100.0%
    [94m•[0m replacing the existing cache path /home/sg/.cache/lamindb/lamindata/result_pbmc3k.h5ad





    Artifact(uid='w2SjnZkk8KyqJMjR0002', key='result_pbmc3k.h5ad', description=None, suffix='.h5ad', kind='dataset', otype='AnnData', size=190901140, hash='l7OrBUr_DM9QK4Omf_3-Fk', n_files=None, n_observations=2638, branch_id=1, created_on_id=1, space_id=1, storage_id=2, run_id=6325, schema_id=None, created_by_id=46, created_at=2026-04-20 09:02:50 UTC, is_locked=False, version_tag=None, is_latest=True)


