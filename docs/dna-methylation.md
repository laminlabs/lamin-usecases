# Methylation

DNA methylation patterns vary with age, disease, and tissue type, which makes them useful for both diagnostics and biological age prediction. 

## A database for methylation profiles

[Ying _et al._ (2024)](https://doi.org/10.1101/2024.10.30.621013) collected 220k human DNA methylation profiles from 5k datasets through the [EWAS Data Hub](https://ngdc.cncb.ac.cn/ewas/datahub) and the [Clockbase agent](https://www.clockbase.org/) and converted the raw files to parquet files. The datasets are available from GitHub in the [MethylGPT](https://github.com/albert-ying/MethylGPT) repo. For reference, the EWAS Data Hub lists 180k samples in April 2026: 

<img width="800" alt="image" src="https://github.com/user-attachments/assets/e903cb39-90ae-4599-8613-949ec1b0c031" />

Ying _et al._'s datasets are available at [lamin.ai/laminlabs/methyldata](https://lamin.ai/laminlabs/methyldata) with additional annotations. You can, e.g., filter by disease status, demographics, or tissue on the UI or with `lamindb`.

## An example use case: age prediction

Here is a [tutorial](https://lamin.ai/laminlabs/methyldata/transform/Jxbyx3uaPNcu000C) where we walk through how to train a ML model to estimate age. 
