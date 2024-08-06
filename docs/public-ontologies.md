# Access public ontologies

This docs section shows how to access public biological ontologies.

For managing in-house ontologies, see {doc}`docs:bio-registries`.

You'll need a lamindb instance with the `bionty` schema module mounted.

```shell
# !pip install 'lamindb[bionty]'
lamin init --storage <storage_name> --schema bionty
```

The guides cover the following entities.

- `Gene` - [Ensembl](https://ensembl.org), [NCBI Gene](https://www.ncbi.nlm.nih.gov/gene)
- `Protein` - [Uniprot](https://www.uniprot.org/)
- `Organism` - [Ensembl Species](https://useast.ensembl.org/info/about/species.html). [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy)
- `CellLine` - [Cell Line Ontology](https://github.com/CLO-ontology/CLO)
- `CellType` - [Cell Ontology](https://obophenotype.github.io/cell-ontology)
- `CellMarker` - [CellMarker](http://xteam.xbio.top/CellMarker)
- `Tissue` - [Uberon](http://obophenotype.github.io/uberon)
- `Disease` - [Mondo](https://mondo.monarchinitiative.org), [Human Disease](https://disease-ontology.org), [ICD](https://www.who.int/standards/classifications/classification-of-diseases)
- `Phenotype` - [Human Phenotype](https://hpo.jax.org/app), [Phecodes](https://phewascatalog.org/phecodes_icd10), [PATO](https://github.com/pato-ontology/pato), [Mammalian Phenotype](http://obofoundry.org/ontology/mp.html), [Zebrafish Phenotype](http://obofoundry.org/ontology/zp.html)
- `Pathway` - [Gene Ontology](https://bioportal.bioontology.org/ontologies/GO), [Pathway Ontology](https://bioportal.bioontology.org/ontologies/PW)
- `ExperimentalFactor` - [Experimental Factor Ontology](https://www.ebi.ac.uk/ols/ontologies/efo)
- `DevelopmentalStage` - [Human Developmental Stages](https://github.com/obophenotype/developmental-stage-ontologies/wiki/HsapDv), [Mouse Developmental Stages](https://github.com/obophenotype/developmental-stage-ontologies/wiki/MmusDv)
- `Drug` - [Drug Ontology](https://bioportal.bioontology.org/ontologies/DRON)
- `Ethnicity` - [Human Ancestry Ontology](https://github.com/EBISPOT/hancestro)

You can see all suported ontology versions [here](https://github.com/laminlabs/bionty/blob/main/bionty/base/sources.yaml).

```{toctree}
:maxdepth: 1
:hidden:

gene
protein
organism
cell_line
cell_type
cell_marker
tissue
disease
phenotype
pathway
experimental_factor
developmental_stage
ethnicity
```
