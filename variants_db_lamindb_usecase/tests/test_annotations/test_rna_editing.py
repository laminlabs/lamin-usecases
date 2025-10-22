import pytest
import pandas as pd
from mutation_db.annotations.rna_editing import read_edits, add_edits


class TestReadEdits:
    def test_reads_edits_file(self, temp_edits_file):
        result = read_edits(str(temp_edits_file))
        assert isinstance(result, dict)
        assert 'chr1' in result
        assert 100 in result['chr1']

    def test_handles_missing_file(self):
        with pytest.raises(SystemExit):
            read_edits("nonexistent_file.txt")

    def test_creates_position_offsets(self, temp_edits_file):
        result = read_edits(str(temp_edits_file))
        assert 99 in result['chr1']
        assert 100 in result['chr1']
        assert 101 in result['chr1']


class TestAddEdits:
   def test_adds_edits_column(self, sample_vcf_data, temp_edits_file, mocker):
        mocker.patch('mutation_db.annotations.rna_editing.read_edits',
                     return_value={'chr1': {100: 1, 200: 1}})
        mocker.patch('mutation_db.annotations.ontology.loading_artifacts_from_collection',
                     return_value=([sample_vcf_data], [mocker.Mock()]))
        result = add_edits()
        assert len(result) > 0

   def test_identifies_editing_sites(self, temp_edits_file):
        df = pd.DataFrame({
            'chrom': ['chr1', 'chr2'],
            'pos': [100, 300]
        })
        edits = read_edits(str(temp_edits_file))
        df['edits'] = df.apply(
            lambda row: row['chrom'] in edits and row['pos'] in edits[row['chrom']],
            axis=1
        )
        assert df.iloc[0]['edits'] == True  # chr1:100 is an edit
        assert df.iloc[1]['edits'] == False  # chr2:300 is not