from pathlib import Path
import lamindb as ln
from downloading_mut_db import build_mutation_collection
from adding_muatations_to_vcf_db import  *
from adding_kegg_annotations import *


ln.connect("biocoder1001/mutation_db_bionty")
ln.track()
if __name__ == "__main__":
    #vcf_folder = Path("/Volumes/CCHL-User/Ishita")  # adjust if needed
    add_kegg_to_vcf()

ln.finish()
