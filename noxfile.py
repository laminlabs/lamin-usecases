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
    "bulkrna.ipynb",
    "facs.ipynb",
    "spatial.ipynb",
    "multimodal.ipynb",
]
GROUPS["by_registry"] = [
    "celltypist.ipynb",
    "enrichr.ipynb",
    # these could be bucketed elsewhere
    "analysis-flow.ipynb",
    "project-flow.ipynb",
]


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
@nox.parametrize(
    "group",
    ["by_datatype", "by_registry", "docs"],
)
def install(session, group):
    extras = ""
    session.run(*"pip install pandas<2.1")
    if group == "by_datatype":
        extras += ",fcs,jupyter"
        session.run(*"pip install scanpy".split())
        session.run(*"pip install mudata".split())
    elif group == "by_registry":
        extras += ",zarr,jupyter"
        session.run(*"pip install celltypist".split())
        session.run(*"pip install gseapy".split())
    elif group == "docs":
        extras += ""
    session.run(*"pip install .".split())
    session.run(
        "pip",
        "install",
        f"lamindb[dev,bionty{extras}] @"
        " git+https://github.com/laminlabs/lamindb@release",
    )


@nox.session
@nox.parametrize(
    "group",
    ["by_datatype", "by_registry"],
)
def build(session, group):
    login_testuser2(session)
    login_testuser1(session)
    session.run(*f"pytest -s ./tests/test_notebooks.py::test_{group}".split())
    # move artifacts into right place
    target_dir = Path(f"./docs_{group}")
    target_dir.mkdir(exist_ok=True)
    for filename in GROUPS[group]:
        shutil.copy(Path("docs") / filename, target_dir / filename)


@nox.session
def docs(session):
    # move artifacts into right place
    for group in ["by_datatype", "by_registry"]:
        for path in Path(f"./docs_{group}").glob("*"):
            path.rename(f"./docs/{path.name}")
    login_testuser1(session)
    session.run(*"lamin init --storage ./docsbuild --schema bionty".split())
    build_docs(session, strict=True)
    upload_docs_artifact(aws=True)
