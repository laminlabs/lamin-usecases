# Test basic imports
try:
    from mutation_db.core import vcf_parser
    from mutation_db.annotations import kegg
    from mutation_db.annotations import ontology
    print("✓ All imports successful!")
except ImportError as e:
    print(f"✗ Import failed: {e}")
