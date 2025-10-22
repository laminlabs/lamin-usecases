import pandas as pd
import tempfile
import pytest
from pathlib import Path

@pytest.fixture
def sample_vcf_data():
    return pd.DataFrame({
        'chrom': ['chr1', 'chr1', 'chr2'],
        'pos': [100, 200, 300],
        'ref': ['A', 'G', 'C'],
        'alt': ['T', 'A', 'G'],
        'gene': ['BRCA1', 'TP53', 'EGFR'],
        'mutation_type': ['snp', 'snp', 'indel'],
        'strand': ['+', '-', '+'],
        'tandem_repeat': [False, False, True],
        'repeat_unit': [None, None, 'AT'],
        'repeat_ref': [None, None, '10'],
        'repeat_alt': [None, None, '12'],
        'repeat_type': [None, None, 'dinucleotide']
    })

@pytest.fixture
def sample_kegg_response():
    """Mock KEGG API response"""
    return """hsa:672\tBRCA1, BRCAI, BRCC1, FANCS, IRIS, PNCA4, PPP1R53, PSCP, RNF53; BRCA1 DNA repair associated
hsa:7157\tTP53, BCC7, LFS1, P53, TRP53; tumor protein p53"""


@pytest.fixture
def sample_pathway_response():
    """Mock pathway API response"""
    return """hsa:672\tpath:hsa05200
hsa:672\tpath:hsa05212"""

@pytest.fixture
def temp_vcf_file():
    """Create a temporary VCF file for testing"""
    vcf_content = """##fileformat=VCFv4.2
##INFO=<ID=GENEINFO,Number=1,Type=String,Description="Gene name">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\t.\tA\tT\t.\t.\tGENEINFO=BRCA1:672
chr1\t200\t.\tG\tA\t.\t.\tGENEINFO=TP53:7157
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vcf', delete=False) as f:
        f.write(vcf_content)
        return Path(f.name)

@pytest.fixture
def temp_edits_file():
    """Create temporary RNA editing file"""
    content = """#chr:pos-ref>alt
chr1:100-A>G
chr2:200-C>T
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        return Path(f.name)





