# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: lamindb
#     language: python
#     name: python3
# ---

# %% [markdown]
# # {{ cookiecutter.entity }}

# %% [markdown]
# lamindb provides access to the following public protein ontologies through [lnschema-bionty](https://github.com/laminlabs/lnschema-bionty):
#{% set sources = cookiecutter.sources.split(',') -%}{% for src in sources %}
# {{ src }}
{%- endfor %}
#
# Here we show how to access and search {{ cookiecutter.entity }} ontologies to standardize new data.

# %% [markdown]
# ## Setup

# %%
# !lamin init --storage ./test-{{ cookiecutter.entity|lower }} --schema bionty

# %%
import bionty as bt
import pandas as pd

# %% [markdown]
# ## PublicOntology objects

# %% [markdown]
# Let us create a public ontology accessor with {meth}`~bionty.dev.BioRegistry.public`, which chooses a default public ontology source from {class}`~docs:bionty.PublicSource`.
# It's a [PublicOntology](https://lamin.ai/docs/bionty.dev.publicontology) object, which you can think about as a public registry:

# %%
{{ cookiecutter.entity_lower }}s = bt.{{ cookiecutter.entity }}.public(organism="{{ cookiecutter.organism }}")
{{ cookiecutter.entity_lower }}s

# %% [markdown]
# As for registries, you can export the ontology as a `DataFrame`:

# %%
df = {{ cookiecutter.entity_lower }}s.df()
df.head()

# %% [markdown]
# Unlike registries, you can also export it as a Pronto object via `public.ontology`.

# %% [markdown]
# ## Look up terms

# %% [markdown]
# As for registries, terms can be looked up with auto-complete:

# %%
lookup = {{ cookiecutter.entity_lower }}s.lookup()

# %% [markdown]
# The `.` accessor provides normalized terms (lower case, only contains alphanumeric characters and underscores):

# %%
lookup.{{ cookiecutter.example_value }}

# %% [markdown]
# To look up the exact original strings, convert the lookup object to dict and use the `[]` accessor:

# %%
lookup_dict = lookup.dict()
lookup_dict["{{ cookiecutter.example_dict_value }}"]

# %% [markdown]
# By default, the `name` field is used to generate lookup keys. You can specify another field to look up:

# %%
lookup = {{ cookiecutter.entity_lower }}s.lookup({{ cookiecutter.entity_lower }}s.{{ cookiecutter.alternative_field }})

# %%
lookup.{{ cookiecutter.alternative_field_value }}

# %% [markdown]
# ## Search terms

# %% [markdown]
# Search behaves in the same way as it does for registries:

# %%
{{ cookiecutter.entity_lower }}s.search("{{ cookiecutter.search_value }}").head(3)

# %% [markdown]
# By default, search also covers synonyms:

# %%
{{ cookiecutter.entity_lower }}s.search("{{ cookiecutter.search_synonyms_value }}").head(3)

# %% [markdown]
# You can turn this off synonym by passing `synonyms_field=None`:

# %%
{{ cookiecutter.entity_lower }}s.search("{{ cookiecutter.search_synonyms_value }}", synonyms_field=None).head(3)

# %% [markdown]
# Search another field (default is `.name`):

# %%
{{ cookiecutter.entity_lower }}s.search(
    "{{ cookiecutter.search_query }}",
    field={{ cookiecutter.entity_lower }}s.{{ cookiecutter.search_field }},
).head()

# %% [markdown]
# ## Standardize {{ cookiecutter.entity }} identifiers

# %% [markdown]
# Let us generate a `DataFrame` that stores a number of {{ cookiecutter.entity }} identifiers, some of which corrupted:

# %%
df_orig = pd.DataFrame(
    index=[{% set identifiers = cookiecutter.identifiers.split(',') -%}{% for identifier in identifiers %}
        "{{ identifier }}"
        {%- endfor %}
        "This {{ cookiecutter.entity_lower }} does not exist",
    ]
)
df_orig

# %% [markdown]
# We can check whether any of our values are validated against the ontology reference:

# %%
validated = {{ cookiecutter.entity_lower }}s.validate(df_orig.index, {{ cookiecutter.entity_lower }}s.name)
df_orig.index[~validated]

# %% [markdown]
# ## Ontology source versions

# %% [markdown]
# For any given entity, we can choose from a number of versions:

# %%
bt.PublicSource.filter(entity="{{ cookiecutter.entity }}").df()

# %% [markdown]
# When instantiating a Bionty object, we can choose a source or version:

# %%
public_source = bt.PublicSource.filter(
    source="{{ cookiecutter.database }}", version="{{ cookiecutter.version }}", organism="{{ cookiecutter.organism }}"
).one()
{{ cookiecutter.entity_lower }}s= bt.{{ cookiecutter.entity }}.public(public_source=public_source)
{{ cookiecutter.entity_lower }}s
# %% [markdown]
# The currently used ontologies can be displayed using:

# %% tags=["hide-output"]
bt.PublicSource.filter(currently_used=True).df()

# %% tags=["hide-cell"]
# !lamin delete --force test-{{ cookiecutter.entity|lower }}
# !rm -r test-{{ cookiecutter.entity|lower }}
