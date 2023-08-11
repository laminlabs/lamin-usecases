"""Examples built using Lamin.

Import the package::

   import lamin_usecases

"""

__version__ = "0.0.1"  # denote a pre-release for 0.1.0 with 0.1rc1

from . import _datasets as datasets

GROUPS = {}
GROUPS["by_datatype"] = [
    "scrna.ipynb",
    "scrna2.ipynb",
    "bulkrna.ipynb",
    "flow.ipynb",
    "spatial.ipynb",
    "multimodal.ipynb",
]
GROUPS["by_registry"] = [
    "celltypist.ipynb",
    "enrichr.ipynb",
    # these could be bucketed elsewhere
    "analysis-flow.ipynb",
    "birds-eye.ipynb",
]
