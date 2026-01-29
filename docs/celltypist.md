---
execute_via: python
---

# CellTypist

Here, we register the immune cell type vocabulary from [CellTypist](https://www.celltypist.org), a computational tool used for cell type classification in scRNA-seq data.

In the following [Cell type annotation and pathway analysis](analysis-registries) guide, we will re-use this vocabulary.

```python
# pip install lamindb
!lamin init --storage ./use-cases-registries --modules bionty
```

```python
import lamindb as ln
import bionty as bt
import pandas as pd
```

## Access CellTypist records ![](https://img.shields.io/badge/Access-10b981)

As a first step we will read in CellTypist's immune cell encyclopedia

```python
description = "CellTypist Pan Immune Atlas v2: basic cell type information"
celltypist_source_v2_url = "https://github.com/Teichlab/celltypist_wiki/raw/main/atlases/Pan_Immune_CellTypist/v2/tables/Basic_celltype_information.xlsx"

celltypist_df = pd.read_excel(celltypist_source_v2_url)
```

It provides an `ontology_id` of the public Cell Ontology for the majority of records.

```python
celltypist_df.head()
```

The "Cell Ontology ID" is associated with multiple "Low-hierarchy cell types":

```python
celltypist_df.set_index(["Cell Ontology ID", "Low-hierarchy cell types"]).head(10)
```

## Validate CellTypist records ![](https://img.shields.io/badge/Validate-10b981)

For any cell type record that can be validated against the public Cell Ontology, we'd like to ensure that it's actually validated.

This will avoid that we'll refer to the same cell type with different identifiers.

We need a public ontology for this. Let's first get the `CL` ontology source.

```python
source = bt.Source.get(name="cl")
source
```

```python
bionty = bt.CellType.public(source=source)
bionty
```

We can now validate the `"Cell Ontology ID"` column:

```python
bionty.inspect(celltypist_df["Cell Ontology ID"], bionty.ontology_id);
```

This looks good! But when inspecting the names, most of them don't validate:

```python
bionty.inspect(celltypist_df["Low-hierarchy cell types"], bionty.name);
```

A search tells us that terms that are named in plural in Cell Typist occur with a name in singular in the Cell Ontology:

```python
celltypist_df["Low-hierarchy cell types"][0]
```

```python
bionty.search(celltypist_df["Low-hierarchy cell types"][0]).head(2)
```

Let's try to strip `"s"` and inspect if more names are now validated. Yes, there are!

```python
bionty.inspect(
    [i.rstrip("s") for i in celltypist_df["Low-hierarchy cell types"]], field="name"
);
```

Every "low-hierarchy cell type" has an ontology id and most "high-hierarchy cell types" also appear as "low-hierarchy cell types" in the Cell Typist table. Four, however, don't, and therefore don't have an ontology ID.

```python
high_terms = celltypist_df["High-hierarchy cell types"].unique()
low_terms = celltypist_df["Low-hierarchy cell types"].unique()

high_terms_nonval = set(high_terms).difference(low_terms)
high_terms_nonval
```

## Register CellTypist records ![](https://img.shields.io/badge/Register-10b981)

Let's first add the "High-hierarchy cell types" as a column `"parent"`.

This enables LaminDB to populate the `parents` and `children` fields, which will enable you to query for hierarchical relationships.

```python
celltypist_df["parent"] = celltypist_df.pop("High-hierarchy cell types")

# if high and low terms are the same, no parents
celltypist_df.loc[
    (celltypist_df["parent"] == celltypist_df["Low-hierarchy cell types"]), "parent"
] = None

# rename columns, drop markers
celltypist_df.drop(columns=["Curated markers"], inplace=True)
celltypist_df.rename(
    columns={"Low-hierarchy cell types": "ct_name", "Cell Ontology ID": "ontology_id"},
    inplace=True,
)
celltypist_df.columns = celltypist_df.columns.str.lower()

# add standardize names for each ontology_id
celltypist_df["name"] = (
    bionty.to_dataframe().loc[celltypist_df["ontology_id"]].name.values
)
```

```python
celltypist_df.head(2)
```

Now, let's create records from the public ontology:

```python
public_records = bt.CellType.from_values(
    celltypist_df.ontology_id, bt.CellType.ontology_id
).save()
```

Let's now amend public ontology records so that they maintain additional annotations that Cell Typist might have.

```python
public_records_dict = {r.ontology_id: r for r in public_records}

for _, row in celltypist_df.iterrows():
    record = public_records_dict[row["ontology_id"]]
    try:
        record.add_synonym(row["ct_name"])
    except (
        ln.errors.ValidationError
    ):  # do nothing if the synonym already exists as a record
        pass
```

### Add parent-child relationship of the records from Celltypist

We still need to add the renaming 4 High hierarchy terms:

```python
list(high_terms_nonval)
```

Let's get the top hits from a search:

```python
for term in list(high_terms_nonval):
    print(f"Term: {term}")
    display(bionty.search(term).head(2))
```

So we decide to:

- Add the "T cells" to the synonyms of the public "T cell" record
- Create the remaining 3 terms only using their names (we think "B cell flow" shouldn't be identified with "B cell")

```python
for name in high_terms_nonval:
    if name == "T cells":
        record = bt.CellType.from_source(name="T cell")
        record.add_synonym(name)
        record.save()
    elif name == "Erythroid":
        record = bt.CellType.from_source(name="erythroid lineage cell")
        record.add_synonym(name)
        record.save()
    else:
        record = bt.CellType(name=name)
        record.save()
```

```python
high_terms_nonval
```

```python
bt.CellType(name="B-cell lineage").save()
```

Now let's add the parent records:

```python
celltypist_df["parent"] = bt.CellType.standardize(celltypist_df["parent"])
```

```python
for _, row in celltypist_df.iterrows():
    record = public_records_dict[row["ontology_id"]]
    if row["parent"] is not None:
        parent_record = bt.CellType.get(name=row["parent"])
        record.parents.add(parent_record)
```

## Access the registry

The previously added CellTypist ontology registry is now available in LaminDB.
To retrieve the full ontology table as a Pandas DataFrame we can use `.filter`:

```python
bt.CellType.to_dataframe()
```

This enables us to look for cell types by creating a lookup object from our new `CellType` registry.

```python
db_lookup = bt.CellType.lookup()
```

```python
db_lookup.memory_b_cell
```

See cell type hierarchy:

```python
db_lookup.memory_b_cell.view_parents()
```

Access parents of a record:

```python
db_lookup.memory_b_cell.parents.to_list()
```
