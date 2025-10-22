import pytest
import pandas as pd
from mutation_db.annotations.kegg import (
    symbol_to_kegg_ids,
    get_pathways_for_kegg_ids,
    names_for_pathways,
    enrich_df_with_kegg_ids
)


class TestSymbolToKeggIDs:
    def test_symbol_to_kegg_ids_returns_list(self, mocker):
        mock_response = mocker.Mock()
        mock_response.ok = True
        mock_response.text = "hsa:672\tBRCA1; BRCA1 DNA repair associated"
        mocker.patch('requests.get', return_value=mock_response)
        result = symbol_to_kegg_ids("BRCA1", "hsa")

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    def test_symbol_to_kegg_ids_matches_exact_gene(self, mocker):
        mock_response = mocker.Mock()
        mock_response.ok = True
        mock_response.text = """hsa:672\tBRCA1, BRCAI; BRCA1 DNA repair
hsa:673\tBRCA1L; BRCA1-like protein"""
        mocker.patch('requests.get', return_value=mock_response)
        result = symbol_to_kegg_ids("BRCA1", "hsa")
        assert "hsa:672" in result
        assert "hsa:673" not in result

    def test_symbol_to_kegg_ids_handles_empty_response(self, mocker):
        mock_response = mocker.Mock()
        mock_response.ok = False
        mocker.patch('requests.get', return_value=mock_response)
        result = symbol_to_kegg_ids("FAKEGENE", "hsa")
        assert result == []


class TestEnrichDFWithKeggIDs:
    def test_adds_kegg_columns(self, sample_vcf_data, mocker):
        mocker.patch('mutation_db.annotations.kegg.symbol_to_kegg_ids',
                     return_value=['hsa:672'])
        mocker.patch('mutation_db.annotations.kegg.get_pathways_for_kegg_ids',
                     return_value=['path:hsa05200'])
        mocker.patch('mutation_db.annotations.kegg.names_for_pathways',
                     return_value='Pathways in cancer')
        result = enrich_df_with_kegg_ids(sample_vcf_data)
        assert 'KEGG_IDs' in result.columns
        assert 'Pathway_IDs' in result.columns
        assert 'Pathway_Names' in result.columns

    def test_handles_genes_without_kegg_ids(self, mocker):
        df = pd.DataFrame({'gene': ['FAKEGENE']})
        mocker.patch('mutation_db.annotations.kegg.symbol_to_kegg_ids',
                     return_value=[])
        result = enrich_df_with_kegg_ids(df)
        assert result['KEGG_IDs'].iloc[0] is None
        assert result['Pathway_IDs'].iloc[0] is None