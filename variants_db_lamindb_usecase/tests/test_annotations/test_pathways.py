import pytest
import pandas as pd
from mutation_db.annotations.ontology import gene_to_pathways


class TestGeneToPathways:
    def test_adds_pathway_column(self, sample_vcf_data, mocker):
        mock_pathways = mocker.Mock()
        mock_pathways.genes.to_list.return_value = ['BRCA1', 'TP53']
        mock_pathways.ontology_id = 'GO:0006281'

        mocker.patch('bionty.Pathway.filter', return_value=[mock_pathways])
        mocker.patch('mutation_db.annotations.ontology.loading_artifacts_from_collection',
                     return_value=([sample_vcf_data], [mocker.Mock()]))
        result = gene_to_pathways()
        assert len(result) > 0

    def test_handles_genes_without_pathways(self, mocker):
        df = pd.DataFrame({'gene': ['UNKNOWNGENE']})
        mocker.patch('bionty.Pathway.filter', return_value=[])
        mocker.patch('mutation_db.annotations.ontology.loading_artifacts_from_collection',
                     return_value=([df], [mocker.Mock()]))
        result = gene_to_pathways()
        assert len(result) > 0