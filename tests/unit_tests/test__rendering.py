"""Assert the template renders into a correct, complete, importable project.

These are the checks worth running on every edit. They catch the failures that
actually happen when editing a cookiecutter template -- an unrendered
placeholder, a file that stopped being copied, a Jinja conditional that emits
the wrong branch -- in about a second, without building a wheel.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

from tests.consts import PROJECT_DIR
from tests.fixtures.rendered_project import (
    PACKAGE_IMPORT_NAME,
    REPO_NAME,
)

TEMPLATE_DIR = PROJECT_DIR / "{{cookiecutter.repo_name}}"

# Paths every generated project must contain, relative to its root.
EXPECTED_PATHS = [
    f"src/{PACKAGE_IMPORT_NAME}/__init__.py",
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/consts.py",
    "tests/unit_tests/__init__.py",
    "pyproject.toml",
    "version.txt",
    "Makefile",
    "run.sh",
    ".pre-commit-config.yaml",
    ".gitignore",
    "README.md",
    "CLAUDE.md",
    "HARNESS-ATTRIBUTION.md",
    ".claude/settings.json",
    "context/01_Solution_Overview/Project_Overview.md",
    "context/02_Domain_Knowledge/Domain_Glossary.md",
    "context/05_AI_Rules_And_Context/FAILURE-MODE-REGISTRY.md",
    "context/07_Code_Patterns/Code_Patterns_Index.md",
]


def test__expected_paths_exist(rendered_project: Path):
    """Every path a generated project is supposed to have is present."""
    missing = [p for p in EXPECTED_PATHS if not (rendered_project / p).exists()]
    assert not missing, f"missing from the generated project: {missing}"


def test__no_unrendered_placeholders(rendered_project: Path):
    """No `cookiecutter.` placeholder survives into a rendered file.

    A leftover placeholder means a misspelled variable or a path wrongly listed
    in `_copy_without_render`. Files under `.claude/skills/` are exempt: they are
    copied verbatim on purpose, so Jinja never substitutes anything in them.
    """
    offenders = []
    for path in rendered_project.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(rendered_project).as_posix()
        if relative.startswith(".claude/skills/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "cookiecutter." in text:
            offenders.append(relative)
    assert not offenders, f"unrendered cookiecutter placeholders in: {offenders}"


def test__no_template_directory_name_leaks(rendered_project: Path):
    """The literal template directory name does not appear in any rendered path."""
    leaks = [
        p.relative_to(rendered_project).as_posix()
        for p in rendered_project.rglob("*")
        if "{{" in p.name
    ]
    assert not leaks, f"unrendered path components: {leaks}"


def test__package_directory_is_named_from_the_prompt(rendered_project: Path):
    """`src/` contains exactly the package named by `package_import_name`."""
    packages = sorted(p.name for p in (rendered_project / "src").iterdir() if p.is_dir())
    assert packages == [PACKAGE_IMPORT_NAME]


def test__package_is_importable(rendered_project: Path):
    """The generated package imports from source, without being installed.

    Guards against a rendered `__init__.py` that is syntactically broken, which
    no amount of file-existence checking would catch.
    """
    init_py = rendered_project / "src" / PACKAGE_IMPORT_NAME / "__init__.py"
    spec = importlib.util.spec_from_file_location(PACKAGE_IMPORT_NAME, init_py)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(PACKAGE_IMPORT_NAME, None)


def test__pyproject_declares_the_distribution_name(rendered_project: Path):
    """`pyproject.toml` parses and names the distribution from `repo_name`."""
    tomllib = pytest.importorskip(
        "tomllib", reason="tomllib is standard library on Python 3.11+"
    )
    with open(rendered_project / "pyproject.toml", "rb") as handle:
        config = tomllib.load(handle)
    assert config["project"]["name"] == REPO_NAME
    assert config["project"]["dynamic"] == ["version"]
    assert config["tool"]["setuptools"]["dynamic"]["version"] == {"file": "version.txt"}


def test__version_is_sourced_only_from_version_txt(rendered_project: Path):
    """`version.txt` is readable and `[project]` declares no static version.

    The version must be dynamic. A static `[project].version` alongside
    `dynamic = ["version"]` is rejected by the build backend, and a static one
    without it silently diverges from version.txt.
    """
    assert (rendered_project / "version.txt").read_text(encoding="utf-8").strip()
    tomllib = pytest.importorskip(
        "tomllib", reason="tomllib is standard library on Python 3.11+"
    )
    with open(rendered_project / "pyproject.toml", "rb") as handle:
        config = tomllib.load(handle)
    assert "version" not in config["project"], (
        "[project].version must not be set; the version comes from version.txt "
        "via [tool.setuptools.dynamic]"
    )


def test__skills_are_copied_verbatim(rendered_project: Path):
    """Skill files are byte-identical to the template source.

    They are listed in `_copy_without_render`, so cookiecutter must copy them
    without handing them to Jinja. This is what keeps a stray delimiter in a
    skill from breaking every generation.
    """
    source_dir = TEMPLATE_DIR / ".claude" / "skills"
    rendered_dir = rendered_project / ".claude" / "skills"
    source_files = sorted(p.relative_to(source_dir).as_posix() for p in source_dir.rglob("*.md"))
    rendered_files = sorted(p.relative_to(rendered_dir).as_posix() for p in rendered_dir.rglob("*.md"))
    assert source_files == rendered_files, "skill file set changed during rendering"
    assert source_files, "expected at least one skill to be shipped"
    for relative in source_files:
        assert (source_dir / relative).read_bytes() == (rendered_dir / relative).read_bytes(), (
            f".claude/skills/{relative} was modified during rendering; "
            "it must be copied verbatim via _copy_without_render"
        )


def test__commands_are_rendered_not_copied(rendered_project: Path):
    """Slash commands are rendered, so they can cite the real project name."""
    qa_command = (rendered_project / ".claude" / "commands" / "qa.md").read_text(encoding="utf-8")
    assert REPO_NAME in qa_command


def test__doctrine_matches_the_chosen_variant(rendered_project: Path, rendered_doctrine: str):
    """`harness_doctrine` controls which doctrine sections are emitted."""
    claude_md = (rendered_project / "CLAUDE.md").read_text(encoding="utf-8")
    full_only = ["Vocabulary lock", "Pattern reuse", "Repro kernel", "Reflexion"]
    if rendered_doctrine == "full":
        missing = [s for s in full_only if s not in claude_md]
        assert not missing, f"full doctrine is missing sections: {missing}"
    else:
        leaked = [s for s in full_only if s in claude_md]
        assert not leaked, f"lean doctrine leaked full-only sections: {leaked}"
    # Both variants must keep the core rules, whatever the weight.
    for core in ["READ before EDIT", "YAGNI", "Verification Loop", "Refuter"]:
        assert core in claude_md, f"core doctrine rule missing: {core}"


def test__context_layer_is_pre_seeded_with_real_names(rendered_project: Path):
    """The context layer ships real project facts, not placeholders."""
    patterns = (
        rendered_project / "context" / "07_Code_Patterns" / "Code_Patterns_Index.md"
    ).read_text(encoding="utf-8")
    assert PACKAGE_IMPORT_NAME in patterns
    assert "B-001" in patterns and "D-001" in patterns

    overview = (
        rendered_project / "context" / "01_Solution_Overview" / "Project_Overview.md"
    ).read_text(encoding="utf-8")
    assert REPO_NAME in overview and PACKAGE_IMPORT_NAME in overview


def test__local_memory_output_root_exists(rendered_project: Path):
    """The agent artifact output root is present, so skills have somewhere to write."""
    local_memory = rendered_project / "LOCAL-MEMORY"
    subdirs = sorted(p.name for p in local_memory.iterdir() if p.is_dir())
    assert subdirs == ["AUDIT-LOG", "CURRENT_TASK", "FEEDBACK", "LESSONS"]


def test__generated_project_ships_a_ci_workflow(rendered_project: Path):
    """A generated project gets CI in the directory GitHub actually reads.

    GitHub only reads `.github/workflows/`. A workflow one level up is inert,
    which is how this template previously shipped no CI at all.
    """
    workflows = rendered_project / ".github" / "workflows"
    assert workflows.is_dir(), "no .github/workflows/ directory"
    found = sorted(p.name for p in workflows.glob("*.yml"))
    assert found, "no workflow files in .github/workflows/"
    stray = sorted(p.name for p in (rendered_project / ".github").glob("*.yml"))
    assert not stray, f"workflow(s) outside .github/workflows/ are inert: {stray}"


def test__ci_workflow_is_valid_yaml_with_expressions_intact(rendered_project: Path):
    """The workflow survives rendering as valid YAML, with `${{ }}` preserved.

    The whole file is wrapped in a raw block so GitHub's expression syntax is
    not eaten by Jinja. This asserts that actually happened.
    """
    yaml = pytest.importorskip("yaml", reason="PyYAML ships with pre-commit")
    workflow = rendered_project / ".github" / "workflows" / "build-test-publish.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "${{" in text, "GitHub expressions were consumed during rendering"
    assert "{% raw %}" not in text and "{% endraw %}" not in text, "raw tags leaked"
    parsed = yaml.safe_load(text)
    assert "jobs" in parsed and parsed["jobs"], "workflow declares no jobs"
    # Publishing is irreversible, so it must never be triggered by a plain push.
    for job_name in ("publish-test", "publish-prod"):
        condition = parsed["jobs"][job_name].get("if", "")
        assert "refs/tags/v" in condition, (
            f"{job_name} must be gated on a version tag, not on a branch push"
        )
