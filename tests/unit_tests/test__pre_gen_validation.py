"""Assert the pre-generation hook rejects answers that would break a project.

The hook exists because cookiecutter will happily render anything. These tests
pin the specific inputs that used to produce a silently-unimportable package.
They are fast: validation runs before any file is written, so each case aborts
almost immediately.
"""

import pytest
from cookiecutter.exceptions import (
    FailedHookException,
    OutputDirExistsException,
)
from cookiecutter.main import cookiecutter

from tests.consts import PROJECT_DIR

VALID = {"repo_name": "valid-package", "package_import_name": "valid_package"}


def generate(tmp_path, **overrides):
    """Render the template with VALID answers plus any overrides."""
    context = dict(VALID)
    context.update(overrides)
    return cookiecutter(
        template=str(PROJECT_DIR),
        no_input=True,
        output_dir=str(tmp_path),
        extra_context=context,
    )


@pytest.mark.parametrize(
    "package_import_name, reason",
    [
        ("my-package", "hyphens are not valid in an identifier"),
        ("my package", "spaces are not valid in an identifier"),
        ("9lives", "an identifier cannot start with a digit"),
        ("class", "a Python keyword can never be imported"),
        ("import", "a Python keyword can never be imported"),
        ("", "an empty name is meaningless"),
    ],
)
def test__invalid_package_import_name_aborts_generation(
    tmp_path, package_import_name, reason
):
    """An unimportable `package_import_name` aborts before any file is written."""
    with pytest.raises(FailedHookException):
        generate(tmp_path, package_import_name=package_import_name)
    assert not list(tmp_path.iterdir()), f"no project should exist: {reason}"


@pytest.mark.parametrize("repo_name", ["-leading-hyphen", "trailing-hyphen-"])
def test__invalid_repo_name_aborts_generation(tmp_path, repo_name):
    """A `repo_name` that is not a valid distribution name aborts generation."""
    with pytest.raises(FailedHookException):
        generate(tmp_path, repo_name=repo_name)
    assert not list(tmp_path.iterdir())


def test__empty_repo_name_aborts_generation(tmp_path):
    """An empty `repo_name` aborts, though not via this hook.

    Cookiecutter renders the project directory name and checks it before
    running pre-generation hooks, so an empty name trips its own
    OutputDirExistsException first -- the rendered directory resolves to the
    output directory, which already exists. The contract that matters is that
    nothing is generated, so this test asserts that rather than pinning which
    layer rejects it.
    """
    with pytest.raises((FailedHookException, OutputDirExistsException)):
        generate(tmp_path, repo_name="")
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "overrides",
    [
        {"package_import_name": "json"},
        {"repo_name": "my_package", "package_import_name": "my_package"},
        {"package_import_name": "MyPackage"},
    ],
)
def test__questionable_but_workable_answers_only_warn(tmp_path, overrides):
    """Conventions that are merely unwise do not block generation.

    Shadowing a stdlib module, underscores in a distribution name and a
    non-lowercase module name all produce working packages. The hook warns and
    gets out of the way -- blocking here would be the gate overreaching.
    """
    generate(tmp_path, **overrides)
    assert list(tmp_path.iterdir()), "a warning must not abort generation"


def test__the_documented_happy_path_generates(tmp_path):
    """The exact values the README advertises are accepted."""
    generate(
        tmp_path,
        repo_name="my-awesome-package",
        package_import_name="my_awesome_package",
    )
    assert (tmp_path / "my-awesome-package" / "src" / "my_awesome_package").is_dir()
