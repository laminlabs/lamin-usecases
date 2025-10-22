from Bio.KEGG import REST
import lamindb as ln
import requests
from mutation_db.annotations.ontology import loading_artifacts_from_collection
import time

def symbol_to_kegg_ids(gene_symbol, organism):
    url = f"https://rest.kegg.jp/find/{organism}/{gene_symbol}"
    response = requests.get(url)
    response.raise_for_status()
    if not response.ok or not response.text.strip():
        return []
    matches = []
    for line in response.text.strip().split('\n'):
        if not line.startswith(f'{organism}:'):
            continue
        kegg_id, description = line.split('\t')
        gene_names = [g.strip() for g in description.split(';')[0].split(',')]
        if gene_symbol in gene_names:
            matches.append(kegg_id)
    return matches

def get_pathways_for_kegg_ids(kegg_id):
    url = f"https://rest.kegg.jp/link/pathway/{kegg_id}"
    response = requests.get(url)
    if not response.ok or not response.text.strip():
        return []
    pathways = [line.split('\t')[1] for line in response.text.strip().split('\n')]
    return pathways

def names_for_pathways(pathway_id):
    url = f"https://rest.kegg.jp/get/{pathway_id}"
    response = requests.get(url)
    if not response.ok or not response.text.strip():
        return []
    for l in response.text.strip().split('\n'):
        if l.startswith('NAME'):
            return l.replace('NAME', "").strip()
    return None

def enrich_df_with_kegg_ids(df, gene_col='gene', organism='hsa'):
    cache_kegg = {}
    cache_pathway_names = {}
    kegg_ids_list = []
    pathway_ids_list = []
    pathway_names_list = []

    for gene in df[gene_col]:
        if gene in cache_kegg:
            kegg_ids = cache_kegg[gene]
        else:
            kegg_ids = symbol_to_kegg_ids(gene, organism)
            cache_kegg[gene] = kegg_ids
            time.sleep(0.2)

        if not kegg_ids:
            kegg_ids_list.append(None)
            pathway_ids_list.append(None)
            pathway_names_list.append(None)
            continue

        all_pathways = []
        all_pathway_names = []
        for kid in kegg_ids:
            pids = get_pathways_for_kegg_ids(kid)
            all_pathways.extend(pids)
            for pid in pids:
                if pid not in cache_pathway_names:
                    pname = names_for_pathways(pid)
                    cache_pathway_names[pid] = pname
                    time.sleep(0.1)
                else:
                    pname = cache_pathway_names[pid]
                all_pathway_names.append(pname)

        kegg_ids_list.append("; ".join(kegg_ids))
        pathway_ids_list.append("; ".join(all_pathways) if all_pathways else None)
        pathway_names_list.append("; ".join(all_pathway_names) if all_pathway_names else None)

    df["KEGG_IDs"] = kegg_ids_list
    df["Pathway_IDs"] = pathway_ids_list
    df["Pathway_Names"] = pathway_names_list

    return df

def add_kegg_to_vcf():
    artifacts_with_kegg = []
    dfs, _ = loading_artifacts_from_collection()
    for df in dfs:
        df_with_kegg_ids = enrich_df_with_kegg_ids(df)
        artifact = ln.Artifact.from_df(df_with_kegg_ids, description='VCF + KEGG enrichment').save()
        artifacts_with_kegg.append(artifact)

    ln.Collection(artifacts_with_kegg, key='kegg_terms_mutation_db').save()

















