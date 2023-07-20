from pathlib import Path

DATASETDIR = Path(__file__).parent.resolve() / "data/"
DATASETDIR.mkdir(exist_ok=True)


def anndata_seurat_ifnb(preprocess: bool = True):
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
    from bionty.dev._io import s3_bionty_assets

    filepath = DATASETDIR / "ifnb.h5ad"
    s3_bionty_assets(
        filename="ifnb.h5ad",
        localpath=filepath,
        assets_base_url="s3://lamindb-test",
    )

    adata = ad.read(filepath)
    if preprocess:
        import pandas as pd
        import scanpy as sc

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

        sc.pp.normalize_total(adata)
        sc.pp.log1p(adata)

        # set STIM as class 0, CTRL as class 1, to make categorical
        adata.obs["stim"] = pd.Categorical(
            adata.obs["stim"], categories=["STIM", "CTRL"], ordered=True
        )
        indices = adata.obs.sort_values(["seurat_annotations", "stim"]).index
        adata = adata[indices, :].copy()
        del adata.raw  # gives issues when saving
    return adata
