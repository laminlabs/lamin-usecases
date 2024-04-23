import shutil
from pathlib import Path

import nox
from laminci import upload_docs_artifact
from laminci.nox import build_docs, login_testuser1, login_testuser2, run_pre_commit

nox.options.default_venv_backend = "none"

GROUPS = {}
GROUPS["by_datatype"] = [
    "scrna.ipynb",
    "scrna2.ipynb",
    "scrna3.ipynb",
    "scrna4.ipynb",
    "scrna5.ipynb",
    "bulkrna.ipynb",
    "facs.ipynb",
    "facs2.ipynb",
    "facs3.ipynb",
    "facs4.ipynb",
    "spatial.ipynb",
    "multimodal.ipynb",
]
GROUPS["by_registry"] = [
    # "celltypist.ipynb",
    "enrichr.ipynb",
    "analysis-registries.ipynb",
    # these could be bucketed elsewhere
    "analysis-flow.ipynb",
    "project-flow.ipynb",
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


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
@nox.parametrize(
    "group",
    ["by_datatype", "by_registry", "by_ontology", "docs"],
)
def install(session, group):
    extras = ""
    if group == "by_datatype":
        extras += ",fcs,jupyter"
        session.run(
            *"uv pip install --system anndata==0.9.2".split()
        )  # compatibility with scvi
        session.run(*"uv pip install --system scanpy".split())
        session.run(*"uv pip install --system pytometry".split())
        session.run(*"uv pip install --system mudata".split())
        session.run(*"uv pip install --system scvi-tools".split())
    elif group == "by_registry":
        extras += ",zarr,jupyter"
        session.run(*"uv pip install --system gseapy".split())
    elif group == "by_ontology":
        extras += ",aws,jupyter"
    elif group == "docs":
        extras += ""
    session.run(*"uv pip install --system .[dev]".split())
    session.run(
        "uv",
        "pip",
        "install",
        "--system",
        f"lamindb[dev,bionty{extras}] @ git+https://github.com/laminlabs/lamindb@main",
    )


@nox.session
@nox.parametrize(
    "group",
    ["by_datatype", "by_registry", "by_ontology"],
)
def build(session, group):
    login_testuser2(session)
    login_testuser1(session)
    if group == "by_ontology":
        session.run(*"python ./scripts/entity_generation/generate.py".split())
    session.run(*f"pytest -s ./tests/test_notebooks.py::test_{group}".split())
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
    login_testuser1(session)
    session.run(*"lamin init --storage ./docsbuild --schema bionty".split())
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
