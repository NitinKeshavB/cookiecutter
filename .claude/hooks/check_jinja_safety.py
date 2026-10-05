#!/usr/bin/env python3
"""
Jinja-safety gate for the cookiecutter template tree.

Everything under the template directory is rendered through Jinja2 by
cookiecutter. Stray Jinja delimiters there do not fail loudly at authoring
time -- they fail at *generation* time, for every downstream developer.

The motivating real-world case: a vendored harness file contained the literal
text `{#term-slug}`. `{#` is Jinja2's comment opener, so with no matching `#}`
the whole generation died with:

    TemplateSyntaxError: Missing end of comment tag

This script is the machine-enforced version of that rule. Two entry points,
one implementation:

  * stdin JSON (Claude Code PreToolUse hook) -- inspect a pending Write/Edit
    and exit 2 to block it before the bad bytes ever land on disk.
  * `--scan` -- audit the whole template tree on demand or in CI.

Exit codes: 0 = allow / clean, 1 = usage or internal error, 2 = block / hazards.
"""

import json
import re
import sys
from pathlib import Path

# The template directory whose contents cookiecutter renders through Jinja2.
TEMPLATE_DIR_NAME = "{{cookiecutter.repo_name}}"

# `{{ ... }}` is legitimate only when it reads a cookiecutter variable.
ALLOWED_EXPR = re.compile(r"\{\{-?\s*cookiecutter\.[A-Za-z_][A-Za-z0-9_]*.*?-?\}\}", re.DOTALL)

# `{% ... %}` is legitimate only for these control tags.
ALLOWED_TAGS = frozenset(
    ["raw", "endraw", "if", "elif", "else", "endif", "for", "endfor", "set"]
)

EXPR_OPEN = re.compile(r"\{\{")
TAG_OPEN = re.compile(r"\{%-?\s*(\w+)")
COMMENT_OPEN = "{#"
COMMENT_CLOSE = "#}"

# Only text files can carry Jinja hazards; skip binary-ish payloads.
SKIP_SUFFIXES = frozenset(
    [".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".whl", ".gz", ".zip", ".pyc"]
)


def load_copy_without_render(repo_root: Path):
    """Return the `_copy_without_render` globs declared in cookiecutter.json.

    Files matching these globs are copied verbatim -- cookiecutter never hands
    them to Jinja -- so Jinja syntax inside them is harmless and must not be
    flagged. Reading the real config keeps this gate consistent with it.
    """
    config = repo_root / "cookiecutter.json"
    if not config.is_file():
        return []
    try:
        return list(json.loads(config.read_text(encoding="utf-8")).get("_copy_without_render", []))
    except (json.JSONDecodeError, OSError):
        return []


def template_relative_path(path: Path):
    """Return the path relative to the template dir, or None if outside it."""
    parts = path.parts
    if TEMPLATE_DIR_NAME not in parts:
        return None
    index = parts.index(TEMPLATE_DIR_NAME)
    return "/".join(parts[index + 1 :])


def is_exempt(rel_path: str, globs) -> bool:
    """True when `_copy_without_render` covers this path (so Jinja never sees it)."""
    from fnmatch import fnmatch

    for pattern in globs:
        if fnmatch(rel_path, pattern):
            return True
        # A glob naming a directory also exempts everything beneath it.
        trimmed = pattern.rstrip("/*")
        if trimmed and (rel_path == trimmed or rel_path.startswith(trimmed + "/")):
            return True
    return False


def find_hazards(text: str):
    """Return a list of human-readable Jinja hazards found in `text`."""
    hazards = []

    # Unbalanced comment delimiters -- the failure mode that motivated this gate.
    opens = text.count(COMMENT_OPEN)
    closes = text.count(COMMENT_CLOSE)
    if opens != closes:
        hazards.append(
            "{0} unclosed Jinja comment(s): found {1} '{2}' but {3} '{4}'. "
            "Jinja reads '{2}' as a comment opener and fails with "
            "'Missing end of comment tag'.".format(
                abs(opens - closes), opens, COMMENT_OPEN, closes, COMMENT_CLOSE
            )
        )

    # Expressions that are not cookiecutter variable reads.
    stripped = ALLOWED_EXPR.sub("", text)
    stray_exprs = len(EXPR_OPEN.findall(stripped))
    if stray_exprs:
        hazards.append(
            "{0} Jinja expression opener(s) that do not read a cookiecutter "
            "variable. Wrap literal braces in a raw block.".format(stray_exprs)
        )

    # Control tags outside the allow-list.
    for tag in TAG_OPEN.findall(text):
        if tag not in ALLOWED_TAGS:
            hazards.append(
                "unexpected Jinja tag '{0}'. Allowed: {1}.".format(
                    tag, ", ".join(sorted(ALLOWED_TAGS))
                )
            )

    return hazards


def pending_content(tool_name: str, tool_input: dict) -> str:
    """Extract the text a Write/Edit tool call is about to introduce."""
    if tool_name == "Write":
        return tool_input.get("content", "") or ""
    if tool_name == "Edit":
        return tool_input.get("new_string", "") or ""
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", []) or []
        return "\n".join(e.get("new_string", "") or "" for e in edits)
    return ""


def run_hook() -> int:
    """PreToolUse entry point: read the tool call from stdin, allow or block."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Never block the session on a malformed payload.
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0

    tool_input = payload.get("tool_input", {}) or {}
    raw_path = tool_input.get("file_path", "")
    if not raw_path:
        return 0

    path = Path(raw_path)
    rel_path = template_relative_path(path)
    if rel_path is None:
        return 0

    repo_root = Path(payload.get("cwd") or ".").resolve()
    parts = path.parts
    if TEMPLATE_DIR_NAME in parts:
        repo_root = Path(*parts[: parts.index(TEMPLATE_DIR_NAME)])

    if is_exempt(rel_path, load_copy_without_render(repo_root)):
        return 0

    hazards = find_hazards(pending_content(tool_name, tool_input))
    if not hazards:
        return 0

    sys.stderr.write(
        "BLOCKED by .claude/hooks/check_jinja_safety.py\n\n"
        "{0} is inside the cookiecutter template directory, so cookiecutter "
        "renders it through Jinja2 at generation time.\n\n".format(rel_path)
    )
    for hazard in hazards:
        sys.stderr.write("  - {0}\n".format(hazard))
    sys.stderr.write(
        "\nFix one of these ways:\n"
        "  1. Wrap the literal text in a Jinja raw block so it survives rendering.\n"
        "  2. Add this path to '_copy_without_render' in cookiecutter.json if the\n"
        "     file needs no cookiecutter values at all.\n"
        "  3. Rewrite the text to avoid the delimiter (e.g. single braces).\n"
        "\nVerify with: python3 .claude/hooks/check_jinja_safety.py --scan\n"
    )
    return 2


def run_scan(repo_root: Path) -> int:
    """`--scan` entry point: audit every rendered file in the template tree."""
    template_dir = repo_root / TEMPLATE_DIR_NAME
    if not template_dir.is_dir():
        sys.stderr.write("no template directory at {0}\n".format(template_dir))
        return 1

    globs = load_copy_without_render(repo_root)
    scanned = 0
    exempt = 0
    findings = []

    for path in sorted(template_dir.rglob("*")):
        if not path.is_file() or path.suffix in SKIP_SUFFIXES:
            continue
        rel_path = template_relative_path(path)
        if rel_path is None:
            continue
        if is_exempt(rel_path, globs):
            exempt += 1
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for hazard in find_hazards(text):
            findings.append((rel_path, hazard))

    print("Jinja safety scan of {0}/".format(TEMPLATE_DIR_NAME))
    print("  rendered files scanned : {0}".format(scanned))
    print("  exempt (copy verbatim) : {0}".format(exempt))

    if not findings:
        print("  hazards                : none")
        return 0

    print("  hazards                : {0}".format(len(findings)))
    print("")
    for rel_path, hazard in findings:
        print("  {0}\n      {1}".format(rel_path, hazard))
    return 2


def main() -> int:
    args = sys.argv[1:]
    if not args:
        return run_hook()
    if args[0] == "--scan":
        root = Path(args[1]).resolve() if len(args) > 1 else Path.cwd()
        return run_scan(root)
    sys.stderr.write(__doc__ or "")
    sys.stderr.write("\nusage: check_jinja_safety.py [--scan [REPO_ROOT]]\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
