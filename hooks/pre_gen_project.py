"""Validate the answers before a single file is written.

Cookiecutter happily renders whatever it is given. Without this gate, answering
`package_import_name` with a hyphenated value produced `src/my-package/`, a
`pyproject.toml` whose package-data key was `my-package`, and a README telling
the user to write `from my-package import ...` -- which is a SyntaxError. The
generation exited 0 and nothing warned.

Failing here costs the user one clear message. Failing later costs them a
project that looks fine and cannot be imported.

Cookiecutter runs this file as a Jinja template first, so the values below are
substituted before Python ever sees them. A non-zero exit aborts generation.
"""

import keyword
import re
import sys

PACKAGE_IMPORT_NAME = "{{ cookiecutter.package_import_name }}"
REPO_NAME = "{{ cookiecutter.repo_name }}"

# PEP 503/508: a distribution name is alphanumerics separated by . - or _
VALID_DISTRIBUTION_NAME = re.compile(
    r"^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9._-]*[A-Za-z0-9])$"
)

errors = []
warnings = []


def check_package_import_name():
    """`package_import_name` has to be something you can actually `import`."""
    if not PACKAGE_IMPORT_NAME:
        errors.append("package_import_name is empty.")
        return

    if not PACKAGE_IMPORT_NAME.isidentifier():
        hint = ""
        if "-" in PACKAGE_IMPORT_NAME:
            hint = " Replace '-' with '_': '{0}'.".format(
                PACKAGE_IMPORT_NAME.replace("-", "_")
            )
        elif " " in PACKAGE_IMPORT_NAME:
            hint = " Replace spaces with '_': '{0}'.".format(
                PACKAGE_IMPORT_NAME.replace(" ", "_")
            )
        elif PACKAGE_IMPORT_NAME[:1].isdigit():
            hint = " A module name cannot start with a digit."
        errors.append(
            "package_import_name '{0}' is not a valid Python identifier, so "
            "`import {0}` is a SyntaxError.{1}".format(PACKAGE_IMPORT_NAME, hint)
        )
        return

    if keyword.iskeyword(PACKAGE_IMPORT_NAME):
        errors.append(
            "package_import_name '{0}' is a Python keyword and can never be "
            "imported.".format(PACKAGE_IMPORT_NAME)
        )
        return

    if PACKAGE_IMPORT_NAME != PACKAGE_IMPORT_NAME.lower():
        warnings.append(
            "package_import_name '{0}' is not lowercase. PEP 8 asks for "
            "lowercase module names; '{1}' is conventional.".format(
                PACKAGE_IMPORT_NAME, PACKAGE_IMPORT_NAME.lower()
            )
        )

    if PACKAGE_IMPORT_NAME in sys.stdlib_module_names:
        warnings.append(
            "package_import_name '{0}' shadows a standard library module. It "
            "will work, but it will confuse every reader and some "
            "tooling.".format(PACKAGE_IMPORT_NAME)
        )


def check_repo_name():
    """`repo_name` becomes the directory name and the pip-installable name."""
    if not REPO_NAME:
        errors.append("repo_name is empty.")
        return

    if not VALID_DISTRIBUTION_NAME.match(REPO_NAME):
        errors.append(
            "repo_name '{0}' is not a valid Python distribution name. Use "
            "letters, digits, '-', '_' or '.', starting and ending with a "
            "letter or digit (PEP 503).".format(REPO_NAME)
        )

    if "_" in REPO_NAME:
        warnings.append(
            "repo_name '{0}' contains underscores. Distribution names "
            "conventionally use hyphens ('{1}'), while the *import* name uses "
            "underscores.".format(REPO_NAME, REPO_NAME.replace("_", "-"))
        )


def main():
    """Validate every answer, report all problems at once, then allow or abort."""
    check_package_import_name()
    check_repo_name()

    for warning in warnings:
        sys.stderr.write("WARNING: {0}\n".format(warning))

    if errors:
        sys.stderr.write(
            "\nCannot generate the project -- the answers would produce a "
            "broken package:\n\n"
        )
        for error in errors:
            sys.stderr.write("  - {0}\n".format(error))
        sys.stderr.write(
            "\nRe-run cookiecutter and supply valid values. Reminder:\n"
            "  repo_name           the pip-installable name, e.g. my-awesome-package\n"
            "  package_import_name the importable module, e.g. my_awesome_package\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
