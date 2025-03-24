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
    "ehr",
    "scrna",
    "scrna2",
    "scrna3",
    "scrna4",
    "scrna-mappedcollection",
    "scrna-tiledbsoma",
    "bulkrna",
    "facs",
    "facs2",
    "facs3",
    "facs4",
    "spatial",
    "multimodal",
    "imaging",
    "imaging2",
    "imaging3",
    "imaging4",
]
GROUPS["by_registry"] = [
    "enrichr",
    "celltypist",
    "analysis-registries",
    # these could be bucketed elsewhere
    "analysis-flow",
    "project-flow",
    "rdf-sparql",
]
GROUPS["by_ontology"] = [
    "gene",
    "cell_line",
    "cell_marker",
    "cell_type",
    "developmental_stage",
    "disease",
    "ethnicity",
    "experimental_factor",
    "organism",
    "pathway",
    "phenotype",
    "protein",
    "tissue",
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
        run(
            session,
            "uv pip install --system pytometry dask[dataframe]",
        )  # Dask is needed by datashader
        run(session, "uv pip install --system mudata")
        run(session, "uv pip install --system tiledbsoma")
        run(
            session, "uv pip install --system setuptools<0.78.0"
        )  #  https://github.com/soft-matter/pims/issues/462
        run(session, "uv pip install --system scportrait")
        run(
            session, "uv pip install --system numpy<2"
        )  # https://github.com/scverse/pytometry/issues/80
    elif group == "by_registry":
        extras += ",zarr,jupyter"
        run(
            session, "pip install celltypist"
        )  # uv pulls very old llvmlite for some reason
        run(session, "uv pip install --system gseapy")
        run(session, "uv pip install --system rdflib")
    elif group == "by_ontology":
        extras += ",jupyter"
    elif group == "docs":
        extras += ""
    run(
        session, "uv pip install --system ipywidgets"
    )  # needed to silence the jupyter warning
    run(session, "uv pip install --system .[dev]")
    branch = "main" if IS_PR else "release"
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
        shutil.copy(
            Path("docs") / f"{filename}.ipynb", target_dir / f"{filename}.ipynb"
        )


@nox.session
def docs(session):
    # move artifacts into right place
    for group in ["by_datatype", "by_registry", "by_ontology"]:
        for path in Path(f"./docs_{group}").glob("*"):
            path.rename(f"./docs/{path.name}.ipynb")
    run(session, "lamin init --storage ./docsbuild --modules bionty")
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
