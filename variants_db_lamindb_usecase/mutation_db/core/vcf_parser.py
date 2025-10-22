import lamindb as ln
from cyvcf2 import VCF
from pathlib import Path
import pandas as pd
import tqdm
from tqdm import tqdm
ln.connect("biocoder1001/mutation_db_bionty")
def read_vcf(vcf_path:Path):
    variants = VCF(str(vcf_path))
    records = []

    for record in variants:
        info = record.INFO

        # Base record structure
        rec = {
            "chrom": record.CHROM,
            "pos": record.POS,
            "ref": record.REF,
            "alt": ",".join(record.ALT),
            "gene": info.get("GENEINFO"),
            "mutation_type": record.var_type,
            "strand": info.get("STRAND"),
            "tandem_repeat": False,  # Default False
            "repeat_unit": info.get("RU"),
            "repeat_ref": info.get("REFREP"),
            "repeat_alt": info.get("ALTREP"),
            "repeat_type": info.get("REPTYPE")
        }
        if rec["gene"]:
            rec["gene"] = rec["gene"].split(':')[0]


        if any(k in info for k in ["STR", "TandemRepeat", "RU", "REFREP", "ALTREP", "REPTYPE"]):
            rec["tandem_repeat"] = True

        records.append(rec)

    # Convert all records to a DataFrame
    return pd.DataFrame(records)

def database_to_artifacts(df:pd.DataFrame,description:str):
    artifact = ln.Artifact.from_dataframe(df, description=description).save()
    return artifact

@ln.tracked()
def build_mutation_collection(vcf_folder: Path) -> ln.Collection:
    vcf_files = list(vcf_folder.glob("*.vcf.gz"))
    artifacts = []

    # Loop over all VCF files
    for vcf_file in tqdm(vcf_files, desc="Processing VCF files"):
        df = read_vcf(vcf_file)
        artifact = database_to_artifacts(df, f'{vcf_file}')
        artifacts.append(artifact)

    collection = ln.Collection(artifacts, key="mutation_db/curated_mutations").save()
    return collection


