import lamindb as ln


ln.setup.login("testuser2")

# register the pipeline and track input/output artifacts
transform = ln.Transform(
    name="Cell Ranger",
    version="7.2.0",
    type="pipeline",
    reference="https://www.10xgenomics.com/support/software/cell-ranger/7.2",
)
ln.track(transform=transform)
# access uploaded files as inputs for the pipeline
input_artifacts = ln.Artifact.filter(key__startswith="fastq/perturbseq").all()
input_paths = [artifact.cache() for artifact in input_artifacts]
# register output files
output_artifacts = ln.Artifact.from_dir(
    "./mydata/perturbseq/filtered_feature_bc_matrix/"
)
ln.save(output_artifacts)
