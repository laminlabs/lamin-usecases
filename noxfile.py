import os
import shutil
from pathlib import Path

import nox
from laminci import upload_docs_artifact
from laminci.nox import (
    build_docs,
    install_lamindb,
    login_testuser1,
    login_testuser2,
    run,
    run_pre_commit,
)

nox.options.default_venv_backend = "none"

GROUPS = {}
GROUPS["by_datatype"] = [
    "scrna.ipynb",
    "scrna2.ipynb",
    "scrna3.ipynb",
    "scrna4.ipynb",
    "scrna5.ipynb",
    "scrna6.ipynb",
    "bulkrna.ipynb",
    "facs.ipynb",
    "facs2.ipynb",
    "facs3.ipynb",
    "facs4.ipynb",
    "spatial.ipynb",
    "multimodal.ipynb",
]
GROUPS["by_registry"] = [
    "enrichr.ipynb",
    "celltypist.ipynb",
    "analysis-registries.ipynb",
    # these could be bucketed elsewhere
    "analysis-flow.ipynb",
    "project-flow.ipynb",
    "rdf-sparql.ipynb",
]
GROUPS["by_ontology"] = [
    "gene.ipynb",
    "cell_line.ipynb",
    "cell_marker.ipynb",
    "cell_type.ipynb",
    "developmental_stage.ipynb",
    "disease.ipynb",
    "ethnicity.ipynb",
    "experimental_factor.ipynb",
    "organism.ipynb",
    "pathway.ipynb",
    "phenotype.ipynb",
    "protein.ipynb",
    "tissue.ipynb",
]


IS_PR = os.getenv("GITHUB_EVENT_NAME") != "push"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
@nox.parametrize(
    "group",
    ["by_datatype", "by_registry", "by_ontology", "docs"],
)
def install(session, group):
    extras = "bionty"
    if group == "by_datatype":
        extras += ",fcs,jupyter"
        run(session, "uv pip install --system pytometry")  # includes scanpy
        run(session, "uv pip install --system dask[dataframe]")  # needed by datashader
        run(session, "uv pip install --system mudata")
        run(session, "uv pip install --system torch")
        run(session, "uv pip install --system tiledbsoma")
    elif group == "by_registry":
        extras += ",zarr,jupyter"
        run(
            session, "pip install celltypist"
        )  # uv pulls very old llvmlite for some reason
        run(session, "uv pip install --system gseapy")
        run(session, "uv pip install --system rdflib")
    elif group == "by_ontology":
        extras += ",aws,jupyter"
    elif group == "docs":
        extras += ""
    run(
        session, "uv pip install --system ipywidgets"
    )  # needed to silence the jupyter warning
    run(session, "uv pip install --system .[dev]")
    branch = "main" if IS_PR else "release"  # point back to "release"
    install_lamindb(session, branch=branch, extras=extras)


@nox.session
@nox.parametrize(
    "group",
    ["by_datatype", "by_registry", "by_ontology"],
)
def build(session, group):
    login_testuser2(session)
    login_testuser1(session)
    if group == "by_ontology":
        run(session, "python ./scripts/entity_generation/generate.py")
    run(session, f"pytest -s ./tests/test_notebooks.py::test_{group}")
    # move artifacts into right place
    target_dir = Path(f"./docs_{group}")
    target_dir.mkdir(exist_ok=True)
    for filename in GROUPS[group]:
        shutil.copy(Path("docs") / filename, target_dir / filename)


@nox.session
def docs(session):
    # move artifacts into right place
    for group in ["by_datatype", "by_registry", "by_ontology"]:
        for path in Path(f"./docs_{group}").glob("*"):
            path.rename(f"./docs/{path.name}")
    run(session, "lamin init --storage ./docsbuild --schema bionty")
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
