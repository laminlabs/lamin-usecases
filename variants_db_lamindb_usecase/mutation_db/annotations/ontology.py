import lamindb as ln
import bionty as bt
import pandas as pd
import numpy as np
from collections import defaultdict
from mutation_db.core.vcf_parser import *

def loading_artifacts_from_collection():
    mutation_collection = ln.Collection.get(uid="REnADkNxlCFRzep10000")
    artefacts = mutation_collection.artifacts.all()
    dfs = [artifact.load() for artifact in artefacts]
    return dfs, artefacts

def gene_to_pathways():
    dfs, artefacts = loading_artifacts_from_collection()
    artefacts_with_pathways = []
    gene_to_pathways_for_db = defaultdict(list)

    for pathways in bt.Pathway.filter():
        for genes in pathways.genes.to_list("symbol"):
            gene_to_pathways_for_db[genes].append(pathways.ontology_id)


    for artefact, df in zip(artefacts, dfs):
        if not 'gene' in df.columns:
            print('Gene column not found in {df}')

        df['Pathway'] = df['gene'].apply(lambda x: gene_to_pathways_for_db.get(x, []) if pd.notnull(x) else [])
        new_artifact = database_to_artifacts(df, description='Mutations_with_go_terms').save()
        artefacts_with_pathways.append(new_artifact)

    ln.Collection(artefacts_with_pathways, key='go_terms_mutation_db').save()
    return artefacts_with_pathways







