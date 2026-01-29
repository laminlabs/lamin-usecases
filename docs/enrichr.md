---
execute_via: python
---

# Gene Ontology (GO)

In this notebook we manage a pathway registry based on "2023 GO Biological Process" ontology. We'll walk you through the steps of registering pathways and link them to genes.

In the [Cell type annotation and pathway analysis](analysis-registries) notebook, we'll demonstrate how to perform a pathway enrichment analysis and track the dataset with LaminDB.

```python
# pip install lamindb gseapy
!lamin init --storage ./use-cases-registries --modules bionty
```

```python
import lamindb as ln
import bionty as bt
import gseapy as gp
```

## Fetch GO pathways annotated with human genes using Enrichr

First we fetch the `"GO_Biological_Process_2023"` pathways for humans using [GSEApy](https://github.com/zqfang/GSEApy) which wraps [GSEA](https://www.gsea-msigdb.org/gsea/index.jsp) and [Enrichr](https://maayanlab.cloud/Enrichr/).

```python
go_bp = gp.get_library(name="GO_Biological_Process_2025", organism="Human")
print(f"Number of pathways {len(go_bp)}")
```

```python
go_bp["ATF6-mediated Unfolded Protein Response (GO:0036500)"]
```

Parse out the ontology_id from keys, convert into the format of {ontology_id: (name, genes)}

```python
def parse_ontology_id_from_keys(key):
    """Parse out the ontology id.

    "ATF6-mediated Unfolded Protein Response (GO:0036500)" -> ("GO:0036500", "ATF6-mediated Unfolded Protein Response")
    """
    name, id = key.rsplit(" (", 1)
    return id.rstrip(")"), name
```

```python
go_bp_parsed = {
    parse_ontology_id_from_keys(k)[0]: (parse_ontology_id_from_keys(k)[1], v)
    for k, v in go_bp.items()
}
```

```python
go_bp_parsed["GO:0036500"]
```

## Register pathway ontology in LaminDB

```python
source = bt.Source.get(name="go")
source
```

```python
bionty = bt.Pathway.public(source=source)
bionty
```

Next, we register all the pathways and genes in LaminDB to finally link pathways to genes.

### Register pathway terms

To register the pathways we make use of `.from_values` to directly parse the annotated GO pathway ontology IDs into LaminDB.

```python
pathways = bt.Pathway.from_values(go_bp_parsed.keys(), bt.Pathway.ontology_id).save()
```

### Register gene symbols

Similarly, we use `.from_values` for all Pathway associated genes to register them with LaminDB.

```python
all_genes = bt.Gene.standardize(sum(go_bp.values(), []), organism="human")
genes = bt.Gene.from_values(all_genes, organism="human").save()
```

Manually register the 32 non-validated symbols:

```python
inspect_result = bt.Gene.inspect(all_genes, organism="human")
organism = bt.Organism.get(name="human")

nonval_genes = []
for g in inspect_result.non_validated:
    nonval_genes.append(bt.Gene(symbol=g, organism=organism))

ln.save(nonval_genes)
```

### Link pathway to genes

Now that we are tracking all pathways and genes records, we can link both of them to make the pathways even more queryable.

```python
symbols_genes = {record.symbol: record for record in genes}
```

```python
for pathway in pathways:
    pathway_genes = go_bp_parsed.get(pathway.ontology_id)[1]
    pathway_genes_records = [symbols_genes.get(gene) for gene in pathway_genes]
    pathway.genes.set(pathway_genes_records)
```

Now genes are linked to pathways:

```python
pathway.genes.to_list("symbol")
```

```python
pathway.genes.to_list("ensembl_gene_id")
```
