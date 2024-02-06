# Access public biological ontologies

- User docs: [here](https://lamin.ai/docs/public-ontologies)
- Developer docs: [here](https://lamin.ai/docs/bionty-base)

## Installation

```shell
pip install 'lamindb[bionty]'
```

## Setup

bionty is a plugin of lamindb, initialize an instance with bionty via:

```shell
lamin init --storage <storage_name> --schema bionty
```

## Entities

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

Check out [sources.yaml](https://github.com/laminlabs/bionty-base/blob/main/bionty_base/sources/sources.yaml) for details.

## Examples

Here we show how to access public biological ontologies using lamindb.

```{toctree}
:maxdepth: 1

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

Please refer to - {doc}`docs:bio-registries` to learn how to manage in-house biological registries.
