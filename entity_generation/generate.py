from cookiecutter.main import cookiecutter

template_arguments = {
    "entity": "",
    "example_value": "",
    "example_dict_value": "",
    "alternative_field_value": "",
    "alternative_field": "",
    "search_value": "",
    "search_synonyms_value": "",
    "search_field": "definition",
    "search_query": "",
    "identifiers": "",
    "database": "",
    "version": "",
    "organism": "",
    "sources": "",
}

protein_arguments = {
    "entity": "Protein",
    "example_value": "ac3",
    "example_dict_value": "AC3",
    "alternative_field_value": "rab4a",
    "alternative_field": "gene_symbol",
    "search_value": "RAS",
    "search_synonyms_value": "member of RAS oncogene family like 2B",
    "search_field": "definition",
    "search_query": "RABL2B",
    "identifiers": "A0A024QZ08,X6RLV5,X6RM24,A0A024QZQ1",
    "database": "uniprot",
    "version": "2023-03",
    "organism": "human",
    "sources": "1. [Uniprot](https://www.uniprot.org/)",
}

organism_arguments = {
    "entity": "Organism",
    "example_value": "giant_panda",
    "example_dict_value": "giant panda",
    "alternative_field_value": "ailuropoda_melanoleuca",
    "alternative_field": "scientific_name",
    "search_value": "rabbit",
    "search_synonyms_value": "sapiens",
    "search_field": "scientific_name",
    "search_query": "oryctolagus_cuniculus",
    "identifiers": "spiny chromis,silver-eye,platyfish,california sea lion",
    "database": "ensembl",
    "version": "release-110",
    "organism": "vertebrates",
    "sources": "1. [Ensembl Species](https://useast.ensembl.org/info/about/species.html),2. [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy)",
}


disease_arguments = {
    "entity": "Disease",
    "example_value": "alzheimer_disease",
    "example_dict_value": "Alzheimer disease",
    "alternative_field_value": "mondo_0004975",
    "alternative_field": "ontology_id",
    "search_value": "parkinsons disease",
    "search_synonyms_value": "paralysis agitans",
    "search_field": "definition",
    "search_query": "progressive degenerative disorder of the central nervous system",
    "identifiers": "supraglottis cancer,alexia,trigonitis,paranasal sinus disorder",
    "database": "mondo",
    "version": "2023-04-04",
    "organism": "all",
    "sources": "1. [Mondo](https://mondo.monarchinitiative.org/),2. [Human Disease](https://disease-ontology.org/)",
}

entities_args = [protein_arguments, organism_arguments, disease_arguments]

for entity_args in entities_args:
    cookiecutter(
        template=".",
        no_input=True,
        overwrite_if_exists=True,
        extra_context=entity_args,
    )

# run jupytext

# Move all notebooks up and delete the corresponding folders
