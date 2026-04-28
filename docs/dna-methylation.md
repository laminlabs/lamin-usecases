---
execute_via: python
---

# DNA methylation

DNA methylation patterns vary with age, disease, and tissue type, which makes them useful for both diagnostics and biological age prediction. We built a [LaminDB instance](https://lamin.ai/laminlabs/methyldata) that curates a dataset of over 150,000 human methylation profiles—the same data used to train [MethylGPT](https://github.com/albert-ying/MethylGPT). LaminDB's queryable metadata makes it easy to filter by disease status, analyze demographic composition, or extract tissue-specific data for model training. For more details on the dataset and curation, check out the linked blog.(TODO)


<img src="https://lamin-site-assets.s3.amazonaws.com/.lamindb/14JvZsWs9qkAGO0d0001.png" width="700">

## Example ML Workflow: Age Prediction

We also have a [tutorial](https://lamin.ai/laminlabs/methyldata/transform/Jxbyx3uaPNcu000C), where we walk through how to train a ML model to estimate age using data from our curated and analysis-ready [DNA methylation instance](https://lamin.ai/laminlabs/methyldata). 
