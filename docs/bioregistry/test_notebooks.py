from pathlib import Path

import lamindb as ln
import nbproject_test as test


def test_notebooks():
    nbdir = Path(__file__).parent
    ln.setup.login("testuser1")
    test.execute_notebooks(nbdir, write=True)
