import nox
from laminci import upload_docs_artifact
from laminci.nox import build_docs, login_testuser1, login_testuser2, run_pre_commit

nox.options.default_venv_backend = "none"


@nox.session
def lint(session: nox.Session) -> None:
    run_pre_commit(session)


@nox.session
@nox.parametrize(
    "group",
    ["datatype", "bioregistry"],
)
def install(session, group):
    extras = ""
    if group == "datatype":
        extras += ",fcs,jupyter"
        session.run(*"pip install scanpy".split())
        session.run(*"pip install mudata".split())
    elif group == "bioregistry":
        extras += ",zarr,jupyter"
        session.run(*"pip install celltypist".split())
        session.run(*"pip install gseapy".split())
    session.run(*"pip install .".split())
    session.run(
        "pip",
        "install",
        f"lamindb[dev,bionty{extras}] @ git+https://github.com/laminlabs/lamindb",
    )


@nox.session
@nox.parametrize(
    "group",
    ["datatype", "bioregistry"],
)
def build(session, group):
    login_testuser2(session)
    login_testuser1(session)
    session.run(*f"pytest -s ./docs/{group}".split())


@nox.session
def docs(session):
    login_testuser1(session)
    session.run(*"lamin init --storage ./docsbuild --schema bionty".split())
    build_docs(session, strip_prefix=True, strict=True)
    upload_docs_artifact(aws=True)
