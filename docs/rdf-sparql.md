---
execute_via: python
---

# RDF export & SPARQL queries

SPARQL is a query language used to retrieve and manipulate data stored in Resource Description Framework (RDF) format.
In this tutorial, we demonstrate how lamindb registries can be queried with SPARQL.

```python
import warnings

warnings.filterwarnings("ignore")
```

```python
# pip install 'lamindb[bionty]' rdflib
!lamin connect laminlabs/lamindata
```

```python
import bionty as bt

from rdflib import Graph, Literal, RDF, URIRef
```

Generally, we need to build a directed RDF Graph composed of triple statements.
Such a graph statement is represented by:

1. a node for the subject

2. an arc that goes from a subject to an object for the predicate

3. a node for the object.

Each of the three parts can be identified by a URI.

We can use the `DataFrame` representation of lamindb registries to build a RDF graph.

## Building a RDF graph

```python
diseases = bt.Disease.to_dataframe()
diseases.head()
```

We convert the DataFrame to RDF by generating triples.

```python
rdf_graph = Graph()

namespace = URIRef("http://sparql-example.org/")

for _, row in diseases.iterrows():
    subject = URIRef(namespace + str(row["ontology_id"]))
    rdf_graph.add((subject, RDF.type, URIRef(namespace + "Disease")))
    rdf_graph.add((subject, URIRef(namespace + "name"), Literal(row["name"])))
    rdf_graph.add(
        (subject, URIRef(namespace + "description"), Literal(row["description"]))
    )

rdf_graph
```

Now we can query the RDF graph using SPARQL for the name and associated description:

```python
query = """
SELECT ?name ?description
WHERE {
  ?disease a <http://sparql-example.org/Disease> .
  ?disease <http://sparql-example.org/name> ?name .
  ?disease <http://sparql-example.org/description> ?description .
}
LIMIT 5
"""

for row in rdf_graph.query(query):
    print(f"Name: {row.name}, Description: {row.description}")
```
