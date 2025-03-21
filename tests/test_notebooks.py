import sys
from pathlib import Path

import nbproject_test as test

sys.path[:0] = [str(Path(__file__).parent.parent)]

from noxfile import GROUPS

DOCS = Path(__file__).parents[1] / "docs/"


def _test_group(group_name: str) -> None:
    for filename in GROUPS[group_name]:
        notebook_path = filename + ".ipynb"
        print(notebook_path)
        test.execute_notebooks(DOCS / notebook_path, write=True)


def test_by_datatype() -> None:
    _test_group("by_datatype")


def test_by_registry() -> None:
    _test_group("by_registry")


def test_by_ontology() -> None:
    _test_group("by_ontology")
