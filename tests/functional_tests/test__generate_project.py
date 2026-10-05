"""Test that the cookiecutter template is valid."""
import pytest
from pathlib import Path


@pytest.mark.slow
def test__can_generate_project(project_dir: Path):
    """Test that this cmd does not fail: `cookiecutter <template directory> ...`."""
    assert project_dir.exists()
