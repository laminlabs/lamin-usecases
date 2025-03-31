import sys
from pathlib import Path

import nbproject_test as test

sys.path[:0] = [str(Path(__file__).parent.parent)]

from noxfile import GROUPS

DOCS = Path(__file__).parents[1] / "docs/"


def test_by_datatype():
    for filename in GROUPS["by_datatype"]:
        print(filename)
        test.execute_notebooks(DOCS / filename, write=True)


def test_by_registry():
    for filename in GROUPS["by_registry"]:
        print(filename)
        test.execute_notebooks(DOCS / filename, write=True)


def test_by_ontology():
    for filename in GROUPS["by_ontology"]:
        print(filename)
        test.execute_notebooks(DOCS / filename, write=True)


def test_spatial():
    for filename in GROUPS["spatial"]:
        print(filename)
        test.execute_notebooks(DOCS / filename, write=True)


def test_sc_imaging():
    for filename in GROUPS["sc_imaging"]:
        print(filename)
        test.execute_notebooks(DOCS / filename, write=True)
