import lamindb as ln


# Post-process 3 cellranger output files
ln.settings.transform.stem_uid = "YqmbO6oMXjRj"
ln.settings.transform.version = "2"
ln.track()

output_artifacts = ln.Artifact.filter(
    key__startswith="perturbseq/filtered_feature_bc_matrix"
).all()
input_artifacts = [f.cache() for f in output_artifacts]
output_path = ln.core.datasets.schmidt22_perturbseq(basedir=ln.settings.storage)
output_file = ln.Artifact(output_path, description="perturbseq counts")
output_file.save()
