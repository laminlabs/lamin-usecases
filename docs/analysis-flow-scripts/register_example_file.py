import lamindb as ln
import bionty as bt


ln.settings.transform.stem_uid = "K4wsS5DTYdFp"
ln.settings.transform.version = "0"
ln.track()

# an example dataset that has a few cell type, tissue and disease annotations
adata = ln.core.datasets.anndata_with_obs()

# validate and register features
curate = ln.Curate.from_anndata(
    adata,
    var_index=bt.Gene.ensembl_gene_id,
    categoricals={
        "cell_type": bt.CellType.name,
        "tissue": bt.Tissue.name,
        "disease": bt.Disease.name,
    },
    organism="human",
)
curate.add_validated_from("all")
curate.add_new_from("cell_type")
curate.validate()
curate.save_artifact(description="anndata with obs")

ln.finish()
