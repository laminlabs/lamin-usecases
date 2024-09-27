import lamindb as ln

ln.setup.login("testuser1")
ln.track("qCJPkOuZAi9q0000")

# register output files of the sequencer
upload_dir = ln.core.datasets.dir_scrnaseq_cellranger(
    "perturbseq", basedir=ln.settings.storage.root, output_only=False
)
ln.Artifact(upload_dir.parent / "fastq/perturbseq_R1_001.fastq.gz").save()
ln.Artifact(upload_dir.parent / "fastq/perturbseq_R2_001.fastq.gz").save()

ln.finish()
