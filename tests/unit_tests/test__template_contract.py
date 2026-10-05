"""Assert the generator's own contract holds: cookiecutter.json and Jinja safety.

These tests need no rendering at all, so they are the cheapest signal in the
suite and the first thing to fail when the contract and the template drift
apart.
"""

import json
import subprocess
import sys
from pathlib import Path

from tests.consts import PROJECT_DIR

TEMPLATE_DIR = PROJECT_DIR / "{{cookiecutter.repo_name}}"
COOKIECUTTER_JSON = PROJECT_DIR / "cookiecutter.json"
JINJA_SAFETY_HOOK = PROJECT_DIR / ".claude" / "hooks" / "check_jinja_safety.py"


def load_config() -> dict:
    """Return the parsed cookiecutter.json."""
    return json.loads(COOKIECUTTER_JSON.read_text(encoding="utf-8"))


def test__cookiecutter_json_is_valid_and_declares_the_prompts():
    """The contract parses and declares every variable the template consumes."""
    config = load_config()
    for variable in ["repo_name", "package_import_name", "harness_doctrine"]:
        assert variable in config, f"cookiecutter.json is missing '{variable}'"


def test__every_prompt_has_a_usable_default():
    """Each prompt has a default, so `--no-input` and the test suite work.

    A choice variable defaults to its first entry. A prompt with no default
    breaks every non-interactive generation, including this suite.
    """
    for name, value in load_config().items():
        if name.startswith("_"):
            continue
        if isinstance(value, list):
            assert value, f"choice variable '{name}' has no options"
            assert all(isinstance(option, str) for option in value)
        else:
            assert isinstance(value, str) and value, f"'{name}' has no usable default"


def test__harness_doctrine_offers_lean_and_full():
    """The doctrine weights the template renders conditional sections for."""
    assert load_config()["harness_doctrine"] == ["lean", "full"]


def test__skills_are_exempt_from_rendering():
    """`.claude/skills/*` is in `_copy_without_render`.

    Skills need no cookiecutter values, and exempting them means Jinja never
    parses them -- so prose containing a brace cannot break generation.
    """
    assert ".claude/skills/*" in load_config()["_copy_without_render"]


def test__every_consumed_variable_is_declared():
    """No template file reads a `cookiecutter.<var>` that the contract omits.

    This is the check that catches a one-sided rename: a variable renamed in
    cookiecutter.json but not in the template, or the reverse, would otherwise
    only show up as a leftover placeholder in someone's generated project.
    """
    import re

    declared = set(load_config())
    pattern = re.compile(r"cookiecutter\.([A-Za-z_][A-Za-z0-9_]*)")
    undeclared = {}
    for path in TEMPLATE_DIR.rglob("*"):
        relative = path.relative_to(TEMPLATE_DIR).as_posix()
        if not path.is_file() or relative.startswith(".claude/skills/"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for found in pattern.findall(text) + pattern.findall(relative):
            if found not in declared:
                undeclared.setdefault(found, []).append(relative)
    assert not undeclared, f"template reads variables absent from cookiecutter.json: {undeclared}"


def test__template_tree_has_no_jinja_hazards():
    """The Jinja safety scan is clean.

    Runs the same script that gates edits as a Claude Code hook and commits as a
    pre-commit hook, so all three paths agree.
    """
    result = subprocess.run(
        [sys.executable, str(JINJA_SAFETY_HOOK), "--scan", str(PROJECT_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"Jinja hazards found:\n{result.stdout}\n{result.stderr}"


def test__jinja_safety_hook_blocks_an_unclosed_comment():
    """The safety hook actually rejects the hazard it exists to catch.

    `{#` opens a Jinja comment. Unclosed, it aborts generation with
    "Missing end of comment tag". A gate that does not block is worse than no
    gate, so the gate is tested rather than trusted.
    """
    payload = {
        "tool_name": "Write",
        "cwd": str(PROJECT_DIR),
        "tool_input": {
            "file_path": str(TEMPLATE_DIR / "context" / "Example.md"),
            "content": "a slug anchor like {#term-slug} breaks rendering",
        },
    }
    result = subprocess.run(
        [sys.executable, str(JINJA_SAFETY_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2, "hook should have blocked an unclosed Jinja comment"
    assert "Missing end of comment tag" in result.stderr


def test__jinja_safety_hook_allows_legitimate_cookiecutter_syntax():
    """The hook does not block the syntax the template is built from."""
    payload = {
        "tool_name": "Write",
        "cwd": str(PROJECT_DIR),
        "tool_input": {
            "file_path": str(TEMPLATE_DIR / "context" / "Example.md"),
            "content": (
                "# {{ cookiecutter.repo_name }}\n"
                "import {{cookiecutter.package_import_name}}\n"
                "{% if cookiecutter.harness_doctrine == 'full' %}extra{% endif %}\n"
                "single braces such as {slug} and {ext} are plain text\n"
            ),
        },
    }
    result = subprocess.run(
        [sys.executable, str(JINJA_SAFETY_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"hook wrongly blocked valid syntax:\n{result.stderr}"


def test__jinja_safety_hook_allows_a_balanced_raw_block():
    """A raw block is the documented escape hatch, so the gate must permit it.

    GitHub Actions expressions (`${{ ... }}`) only survive rendering inside a
    raw block. A gate that flagged them would be flagging the fix it recommends.
    """
    payload = {
        "tool_name": "Write",
        "cwd": str(PROJECT_DIR),
        "tool_input": {
            "file_path": str(TEMPLATE_DIR / ".github" / "workflows" / "example.yml"),
            "content": "{% raw %}run: echo ${{ github.sha }} ${{ matrix.python-version }}{% endraw %}\n",
        },
    }
    result = subprocess.run(
        [sys.executable, str(JINJA_SAFETY_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"hook wrongly blocked a raw block:\n{result.stderr}"


def test__jinja_safety_hook_blocks_an_unclosed_raw_block():
    """An unclosed raw block is a hazard in its own right."""
    payload = {
        "tool_name": "Write",
        "cwd": str(PROJECT_DIR),
        "tool_input": {
            "file_path": str(TEMPLATE_DIR / ".github" / "workflows" / "example.yml"),
            "content": "{% raw %}run: echo ${{ github.sha }}\n",
        },
    }
    result = subprocess.run(
        [sys.executable, str(JINJA_SAFETY_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "unbalanced raw block" in result.stderr


def test__cookiecutter_hooks_are_scanned_too():
    """A hazard in `hooks/` is caught: cookiecutter renders hook scripts as well."""
    payload = {
        "tool_name": "Write",
        "cwd": str(PROJECT_DIR),
        "tool_input": {
            "file_path": str(PROJECT_DIR / "hooks" / "pre_gen_project.py"),
            "content": "# an anchor like {#slug} would abort every generation\n",
        },
    }
    result = subprocess.run(
        [sys.executable, str(JINJA_SAFETY_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2, "hooks/ must be scanned; cookiecutter renders it"


def test__claude_hooks_directory_is_not_treated_as_rendered():
    """`.claude/hooks/` is not a cookiecutter hooks directory despite the name.

    It holds the gate's own source, which cookiecutter never renders. Scanning
    it would make the gate flag itself.
    """
    payload = {
        "tool_name": "Edit",
        "cwd": str(PROJECT_DIR),
        "tool_input": {
            "file_path": str(PROJECT_DIR / ".claude" / "hooks" / "check_jinja_safety.py"),
            "new_string": 'COMMENT_OPEN = "{#"\n',
        },
    }
    result = subprocess.run(
        [sys.executable, str(JINJA_SAFETY_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, ".claude/hooks/ must not be scanned as rendered"
