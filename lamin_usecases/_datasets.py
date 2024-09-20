from pathlib import Path
from typing import TYPE_CHECKING

import anndata as ad

DATASETDIR = Path(__file__).parent.resolve() / "data/"
DATASETDIR.mkdir(exist_ok=True)


def anndata_seurat_ifnb(
    preprocess: bool = True, populate_registries: bool = False
) -> ad.AnnData:
    """Seurat ifnb dataset.

    PBMCs were split into a stimulated and control group and the stimulated group was treated with interferon beta.

    To reproduce the format conversion in R:
    >>> library(Seurat)
    >>> library(SeuratDisk)
    >>> library(SeuratData)

    >>> ifnb = SeuratData::LoadData("ifnb")
    >>> ifnb_updated = UpdateSeuratObject(ifnb)
    >>> SaveH5Seurat(ifnb_updated, "ifnb.h5seurat", overwrite = T)
    >>> Convert("ifnb.h5seurat", "ifnb.h5ad", overwrite = T)
    """
    import anndata as ad
    import pandas as pd
    from bionty.base.dev._io import s3_bionty_assets

    filepath = DATASETDIR / "ifnb.h5ad"
    s3_bionty_assets(
        filename="ifnb.h5ad",
        localpath=filepath,
        assets_base_url="s3://lamindb-test",
    )

    adata = ad.read_h5ad(filepath)
    # from https://satijalab.org/seurat/archive/v3.2/immune_alignment.html
    anno_mapper = {
        "0": "CD14 Mono",
        "1": "CD4 Naive T",
        "2": "CD4 Memory T",
        "3": "CD16 Mono",
        "4": "B",
        "5": "CD8 T",
        "6": "NK",
        "7": "T activated",
        "8": "DC",
        "9": "B Activated",
        "10": "Mk",
        "11": "pDC",
        "12": "Eryth",
    }
    adata.obs["seurat_annotations"] = (
        adata.obs["seurat_annotations"].astype(str).map(anno_mapper)
    )
    adata.var.rename(columns={"features": "symbol"}, inplace=True)
    adata.raw.var.rename(columns={"_index": "symbol"}, inplace=True)
    adata.obs.drop(
        columns=["orig.ident", "nCount_RNA", "nFeature_RNA", "seurat_annotations"],
        inplace=True,
    )
    # set STIM as class 0, CTRL as class 1, to make categorical
    adata.obs["stim"] = pd.Categorical(
        adata.obs["stim"], categories=["STIM", "CTRL"], ordered=True
    )
    indices = adata.obs.sort_values(["stim"]).index
    adata = adata[indices, :].copy()
    if preprocess:
        import scanpy as sc

        sc.pp.normalize_total(adata)
        sc.pp.log1p(adata)

    if populate_registries:
        import bionty as bt
        import lamindb as ln

        bt.settings.organism = "human"

        verbosity = ln.settings.verbosity
        ln.settings.verbosity = 0
        adata.var.index = bt.Gene.standardize(adata.var.index)
        validated = bt.Gene.validate(adata.var.index)
        adata = adata[:, validated].copy()
        adata.raw = adata.raw[:, validated].to_adata()
        adata.raw.var.index = adata.var.index
        duplicated = adata.var.index.duplicated()
        adata = adata[:, ~duplicated].copy()
        adata.raw = adata.raw[:, ~duplicated].to_adata()
        adata.raw.var.index = adata.var.index
        ln.save(bt.Gene.from_values(adata.var.index))
        ln.settings.verbosity = verbosity

    return adata


def anndata_mcfarland() -> ad.AnnData:
    """Reduced dataset of McFarland 2020.

    Dataset obtained from https://zenodo.org/record/7041849/files/McFarlandTsherniak2020.h5ad
    Subsampled to 20% of the original data.
    """
    import anndata as ad
    from bionty.base.dev._io import s3_bionty_assets

    filepath = DATASETDIR / "mcfarland.h5ad"
    s3_bionty_assets(
        filename="mcfarland.h5ad",
        localpath=filepath,
        assets_base_url="s3://lamindb-test",
    )

    adata = ad.read_h5ad(filepath)

    return adata
