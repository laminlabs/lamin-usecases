from Bio.KEGG import REST
import lamindb as ln
from lamindb.core.loaders import load_svg

from mutation_db.annotations.ontology import loading_artifacts_from_collection
import time

def mutation_in_tandem_regions():
    dfs, _ = loading_artifacts_from_collection()
    artifacts = []
    number_of_tr_per_df = []
    for df in dfs:
        new_df = df[df['tandem_repeat'].apply(lambda x: x == True)]
        number_of_tr_per_df.append(len(new_df))
        if not new_df.empty:
            artifact = ln.Artifact.from_df(new_df, description='STR_mutations')
            artifact.save()
            artifacts.append(artifact)
            ln.Collection(artifacts, key='STR_db').save()
    return number_of_tr_per_df if number_of_tr_per_df else 0






def snps_database():
    dfs, _ = loading_artifacts_from_collection()
    artifacts = []
    number_of_snps_per_df = []
    for df in dfs:
        new_df = df[df['mutation_type'].apply(lambda x: x == 'snp')]
        number_of_snps_per_df.append(len(new_df))
        artifact = ln.Artifact.from_df(new_df, description='snp_mutations')
        artifact.save()
        artifacts.append(artifact)
    ln.Collection(artifacts, key='snp_db').save()
    return number_of_snps_per_df





