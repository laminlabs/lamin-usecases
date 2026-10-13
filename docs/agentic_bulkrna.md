# Agentic Bulk RNA-seq Analysis

Instead of writing the analysis script manually, you can describe the task in plain English
and let an AI agent write and run it for you — with all inputs and outputs automatically
tracked in LaminDB.

[LaminAgent](https://github.com/laminlabs/laminagent) integrates
[Codex](https://github.com/openai/codex) as an AI agent that reads a skill (a structured
set of instructions stored in LaminDB), writes a Python script tailored to your data, and
executes it — registering every input and output as a LaminDB artifact.

## When to use this

- You have pre-computed DESeq2 results in any tabular format (Excel, CSV, TSV, etc.)
- You want to produce standard visualizations (volcano plot, heatmap) without writing boilerplate
- You want full lineage tracking of inputs and outputs without manual `ln.track()` calls

## Run the agent

```python
import laminagent
from pathlib import Path

laminagent.run_codex(
    run_dir=Path("./my-analysis"),   # directory where your results file lives
    prompt=(
        "Parse the DESeq2 results from my_results.csv, produce a volcano plot and "
        "heatmap of the top 50 differentially expressed genes, and register all "
        "outputs as LaminDB artifacts."
    ),
    skill_uid="XarPyl1XCgZwSQmY0000",
    skill_instance="laminlabs/lamin-skills",
)
```

Point `run_dir` at the directory containing your results file and name it in the prompt.
The agent handles the rest.

## What the agent does

The agent follows the [DESeq2 bulk RNA-seq skill](https://lamin.ai/laminlabs/lamin-skills),
which gives it precise instructions to:

1. **Locate the data** — finds the DE results table regardless of file format or layout,
   scanning sheets and header rows dynamically
2. **Standardize columns** — maps any combination of `log2FoldChange`, `padj`, `SYMBOL`,
   `FDR`, `qval`, etc. to a clean schema
3. **Produce outputs**:
   - `deseq2_results.csv` — cleaned DEG table
   - `volcano_plot.png` — significant genes (padj < 0.05, |log2FC| ≥ 1) highlighted
   - `heatmap_top50.png` — top 50 genes by adjusted p-value
4. **Register everything in LaminDB** — source file and all outputs are saved as artifacts
   with descriptions, so lineage is fully captured

## View lineage

After the run, you can inspect what was produced:

```python
import lamindb as ln

ln.Artifact.filter(description__icontains="DESeq2").df()
```
