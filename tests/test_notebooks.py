from pathlib import Path

import nbproject_test as test

DOCS = Path(__file__).parents[1] / "docs/"


def test_by_datatype():
    test.execute_notebooks(DOCS / "scrna.ipynb", write=True)
    test.execute_notebooks(DOCS / "scrna-1.ipynb", write=True)
    test.execute_notebooks(DOCS / "bulkrna.ipynb", write=True)
    test.execute_notebooks(DOCS / "flow.ipynb", write=True)
    test.execute_notebooks(DOCS / "spatial.ipynb", write=True)
    test.execute_notebooks(DOCS / "multimodal.ipynb", write=True)


def test_by_registry():
    DOCS = Path(__file__).parents[1] / "docs/"
    test.execute_notebooks(DOCS / "celtypist.ipynb", write=True)
    test.execute_notebooks(DOCS / "enrichr.ipynb", write=True)
