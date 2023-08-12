import sys
from pathlib import Path

import nbproject_test as test

sys.path[:0] = [str(Path(__file__).parent.parent)]

from noxfile import GROUPS  # noqa

DOCS = Path(__file__).parents[1] / "docs/"


def test_by_datatype():
    for filename in GROUPS["by_datatype"]:
        print(filename)
        test.execute_notebooks(DOCS / filename, write=True)


def test_by_registry():
    for filename in GROUPS["by_registry"]:
        print(filename)
        test.execute_notebooks(DOCS / filename, write=True)
