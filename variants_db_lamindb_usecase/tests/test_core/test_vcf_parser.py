import pytest
import pandas as pd
from pathlib import Path
from mutation_db.core.vcf_parser import read_vcf
from mutation_db.annotations.ontology import database_to_artifacts
from tests.conftest import  *


class TestReadVCF:

    def test_read_vcf_returns_dataframe(self, temp_vcf_file):
        result = read_vcf(temp_vcf_file)
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_read_vcf_has_required_columns(self, temp_vcf_file):
        df = read_vcf(temp_vcf_file)
        required_columns = ['chrom', 'pos', 'ref', 'alt', 'gene', 'mutation_type']
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

    def test_read_vcf_parses_gene_info(self, temp_vcf_file):
        df = read_vcf(temp_vcf_file)
        assert 'BRCA1' in df['gene'].values
        assert 'TP53' in df['gene'].values

class TestDatabaseToArtifacts:
    def test_creates_artifact_from_dataframe(self, sample_vcf_data, mocker):
        mock_artifact= mocker.Mock()
        mocker.patch('lamindb.Artifact.from_dataframe', return_value=mock_artifact)
        result = database_to_artifacts(sample_vcf_data, "test description")
        assert result == mock_artifact.save()

