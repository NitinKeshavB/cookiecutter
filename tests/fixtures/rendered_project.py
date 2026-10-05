"""Fast, in-process rendering of the template, for the unit test tier.

This fixture deliberately does NOT shell out, `git init`, install anything, or
touch the network. It calls cookiecutter's Python API and nothing else, so the
whole unit tier runs in about a second. The slow end-to-end path -- git, pip,
pre-commit, a wheel built in a throwaway venv -- lives in the functional tier
behind the `slow` marker.
"""

from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

from tests.consts import PROJECT_DIR

# Every value `harness_doctrine` accepts, so both branches of the conditional
# doctrine are rendered and asserted on rather than only the default.
HARNESS_DOCTRINES = ("lean", "full")

REPO_NAME = "test-rendered-package"
PACKAGE_IMPORT_NAME = "test_rendered_package"


@pytest.fixture(scope="session", params=HARNESS_DOCTRINES)
def rendered_project(request, tmp_path_factory) -> Path:
    """Render the template in-process and return the generated project directory.

    Parameterised over `harness_doctrine`, so each test that uses this fixture
    runs once per doctrine variant.
    """
    doctrine: str = request.param
    output_dir = tmp_path_factory.mktemp(f"render-{doctrine}")
    cookiecutter(
        template=str(PROJECT_DIR),
        no_input=True,
        output_dir=str(output_dir),
        extra_context={
            "repo_name": REPO_NAME,
            "package_import_name": PACKAGE_IMPORT_NAME,
            "harness_doctrine": doctrine,
        },
    )
    project_dir = output_dir / REPO_NAME
    assert project_dir.is_dir(), f"cookiecutter did not create {project_dir}"
    return project_dir


@pytest.fixture(scope="session")
def rendered_doctrine(rendered_project: Path) -> str:
    """Return which `harness_doctrine` the current `rendered_project` was built with."""
    text = (rendered_project / "CLAUDE.md").read_text(encoding="utf-8")
    return "full" if "Vocabulary lock" in text else "lean"
