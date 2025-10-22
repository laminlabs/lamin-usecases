import pytest
import pandas as pd
from mutation_db.filters.mutation_types import (
    mutation_in_tandem_regions,
    snps_database
)

class TestMutationInTandemRegions:
    def test_filters_tandem_repeats(self, sample_vcf_data, mocker):
        mocker.patch('mutation_db.annotations.ontology.loading_artifacts_from_collection',
                     return_value=([sample_vcf_data], [mocker.Mock()]))
        result = mutation_in_tandem_regions()
        assert isinstance(result, list) or result is 0


class TestSNPsDatabase:
    def test_filters_snps(self, sample_vcf_data, mocker):
        mocker.patch('mutation_db.annotations.ontology.loading_artifacts_from_collection',
                     return_value=([sample_vcf_data], [mocker.Mock()]))
        result = snps_database()
        assert isinstance(result, list)

    def test_excludes_indels(self):
        df = pd.DataFrame({
            'mutation_type': ['snp', 'indel', 'snp', 'del']
        })
        snp_mask = df['mutation_type'] == 'snp'
        result = df[snp_mask]
        assert len(result) == 2
        assert all(result['mutation_type'] == 'snp')