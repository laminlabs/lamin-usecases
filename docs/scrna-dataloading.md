---
execute_via: python
---

# Use machine learning data loaders

Here, we iterate over the artifacts within a collection to train a machine learning model at scale.

{class}`~lamindb.core.MappedCollection` supports weighted random sampling from `.h5ad` files.
[`annbatch`](https://blog.lamin.ai/annbatch) is a faster alternative for chunked loading from `.zarr` stores.

```python
import lamindb as ln

ln.track()
```

Query our collection:

```python
collection = ln.Collection.get(key="scrna/collection1")
collection.describe()
```

## Create an annbatch loader: sample contiguous chunks

`annbatch` loads contiguous chunks from a collection of `.zarr` stores and much faster than per-cell sampling when you do not need weighted random access. See the [annbatch blog post](https://blog.lamin.ai/annbatch).

In most cases, you should create a shuffled collection, similar to [here](https://lamin.ai/laminlabs/arrayloader-benchmarks/collection/LaJOdLd0xZ3v5ZBw).

```{code-block} python
import anndata as ad
import zarr
from annbatch import Loader

paths = [artifact.cache() for artifact in collection.artifacts.all()]
loader = Loader(shuffle=True, batch_size=4096, chunk_size=256, preload_nchunks=64)
loader.add_datasets(
    datasets=[ad.io.sparse_dataset(zarr.open(p)["X"]) for p in paths],
    obs=[ad.io.read_elem(zarr.open(p)["obs"]) for p in paths],
)
for batch in loader:
    pass
```

## Create a map-style dataset: weighted single-cell sampling

While much slower than, for example, `annbatch`, the following approach enables weighted single-cell sampling.

You create [map-style dataset](https://pytorch.org/docs/stable/data) using {meth}`~lamindb.Collection.mapped`: a {class}`~lamindb.core.MappedCollection`.
Under-the-hood, it performs a virtual join of the features of the underlying `AnnData` objects without loading the datasets into memory. You can either perform an inner join:

```python
with collection.mapped(obs_keys=["cell_type"], join="inner") as dataset:
    print("#observations", dataset.shape[0])
    print("#variables:", len(dataset.var_joint))
```

Or an outer join:

```python
dataset = collection.mapped(obs_keys=["cell_type"], join="outer")
print("#variables:", len(dataset.var_joint))
```

This is compatible with a PyTorch `DataLoader` because it implements `__getitem__` over a list of backed `AnnData` objects.
For instance, the 5th observation in the collection can be accessed via:

```python
dataset[5]
```

The `labels` are encoded into integers:

```python
dataset.encoders
```

It is also possible to create a dataset by selecting only observations with certain values of an `.obs` column. Setting `obs_filter` in the below example makes the dataset iterate only over observations having `CD16-positive, CD56-dim natural killer cell, human` or `macrophage` in `.obs` column `cell_type` across all `AnnData` objects.

```python
select_by_cell_type = (
    "CD16-positive, CD56-dim natural killer cell, human",
    "macrophage",
)

with collection.mapped(obs_filter=("cell_type", select_by_cell_type)) as dataset_filter:
    print(dataset_filter.shape)
```

## Create a pytorch DataLoader

Let us use a weighted sampler:

```python
from torch.utils.data import DataLoader, WeightedRandomSampler

# label_key for weight doesn't have to be in labels on init
sampler = WeightedRandomSampler(
    weights=dataset.get_label_weights("cell_type"), num_samples=len(dataset)
)
dataloader = DataLoader(dataset, batch_size=128, sampler=sampler)
```

We can now iterate through the data loader:

```python
for batch in dataloader:
    pass
```

Close the connections in {class}`~lamindb.core.MappedCollection`:

```python
dataset.close()
```

:::{dropdown} In practice, use a context manager

```
with collection.mapped(obs_keys=["cell_type"]) as dataset:
    sampler = WeightedRandomSampler(
        weights=dataset.get_label_weights("cell_type"), num_samples=len(dataset)
    )
    dataloader = DataLoader(dataset, batch_size=128, sampler=sampler)
    for batch in dataloader:
        pass
```

:::
