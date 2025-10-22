import lamindb as ln
import os
import sys
import re
from mutation_db.annotations.ontology import loading_artifacts_from_collection

def read_edits(filename):
    edits = {}
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = re.split('[:-]', line)
                chrom, pos = parts[0], int(parts[1])
                if chrom not in edits:
                    edits[chrom] = {}
                for offsets in [1, 0, -1]:
                    edits[chrom][pos + offsets] = 1
        if not edits:
            sys.exit(1)
    else:
        sys.exit('The radar file not found')

    return edits

def add_edits():
    artifacts_with_rna_edits_info = []
    edits = read_edits("edits.txt")
    dfs, _ = loading_artifacts_from_collection()
    for df in dfs:
        df['edits'] = df.apply(
            lambda row: row['chrom'] in edits and row['pos'] in edits[row['chrom']],
            axis=1
        )
        artifact = ln.Artifact.from_dataframe(df, description='rna_editing').save()
        artifacts_with_rna_edits_info.append(artifact)

    ln.Collection(artifacts_with_rna_edits_info,key='VCF_with_rna_editing_info').save()
    return artifacts_with_rna_edits_info





