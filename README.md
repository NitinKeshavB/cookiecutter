# Python Package Template for OpenMetadata Catalog

This is a project scaffold to help you quickly get up and running with a Python package using
modern, industry standard tools and practices.

The template comes with an opinionated VS Code settings configuration file to help ensure
the best integration with the tools here, e.g.

- autocompletion
- syntax highlighting
- auto-formatting on save
- red/yellow squiggly lines under linting errors
- automatic discovery of tests so they are executable in the VS Code test explorer

## Quick start

```bash
# install cookiecutter into an isolated virtual environment
python -m venv ./venv/
source ./venv/bin/activate
pip install --upgrade pip
pip install cookiecutter

# cookie cut the template, answering the prompts, e.g.
#  - repo_name: my-awesome-package
#  - package_import_name: my_awesome_package
cookiecutter https://github.com/mlops-club/cloud-course-python-package-cookiecutter.git
```

You will be prompted for:

| Prompt | Meaning | Example |
|--------|---------|---------|
| `repo_name` | the directory and distribution name | `my-awesome-package` |
| `package_import_name` | the importable module name | `my_awesome_package` |
| `harness_doctrine` | how much AI-agent doctrine to ship (`lean` or `full`) | `lean` |

## The AI agent harness

Generated projects ship a [Claude Code](https://claude.com/claude-code) harness so a
coding agent is productive in them immediately: an operational doctrine (`CLAUDE.md`),
seven slash commands, five skills, and a `context/` spec layer that is **pre-seeded
with the project's real layout, toolchain and patterns** rather than left as blank
placeholders.

`harness_doctrine` picks the weight. `lean` carries the core — evidence weights, named
refuters, surgical-change rules and the verification loop. `full` adds vocabulary
locking, pattern reuse, repro kernels and reflexion lessons, which pay off once a
project has accumulated real domain terms and patterns.

This repository has its own, separate harness for working on the template itself —
see `CLAUDE.md` and `.claude/`. Its central rule is the Jinja contract: everything
under `{{cookiecutter.repo_name}}/` is rendered at generation time, so a stray `{{`,
`{%` or `{#` there breaks every generation. That rule is enforced, not merely
documented, by `.claude/hooks/check_jinja_safety.py`, which runs as a Claude Code
`PreToolUse` hook and again in `pre-commit`. Audit it any time with:

```bash
python3 .claude/hooks/check_jinja_safety.py --scan
```

The harness is adapted from the Claude Code Agent Harness by Viacheslav Tronko (MIT);
see `HARNESS-ATTRIBUTION.md` for provenance and the list of deviations.

## What are the opinions in this template?

### Notable comments about the file structure

- `src/<package-name>/` - contains the package code. Using an `src/` folder is a best practice.
- `tests/` has minimal boilerplate that
  - Makes fixtures work using `conftest.py`
  - Makes imports such as `from tests.my_file import thing` (via some *light* PYTHONPATH hacking, adding `tests/..` to the PYTHONPATH)
  - Contains a `unit_test/` and `functional_test/` directory whose structure is meant to mirror that of `src/<package>/`
- `.vscode/`
  - contains `extensions.json` which can be used to install several recommended extensions to get a great development experience
  - contains `settings.json` which configures the various VS Code extensions, e.g. `black` to read their settings from `pyproject.toml`

### Tools

This project template makes use of

- [`setuptools`](https://setuptools.pypa.io/en/latest/userguide/index.html) for packaging; a `pip` + `venv` + `setuptools` workflow is encouraged as it is considered the
  most officially supported, "vanilla" way to manage Python packages.
- [`pylint`](https://pylint.readthedocs.io/en/stable/) and [`flake8`](https://flake8.pycqa.org/en/latest/) for linting. [`ruff`](https://docs.astral.sh/ruff/) is up and coming, but does not yet support all the plugins and rulesets
  that these two do. However, we love `ruff` and are excitedly watching its progress.
  - [`flake8`](https://flake8.pycqa.org/en/latest/) supports plugins, and we are using the following
    - [`flake8-docstrings`](https://pypi.org/project/flake8-docstrings/) - ensure that functions have docstrings
    - [`flake8-pyproject`](https://pypi.org/project/Flake8-pyproject/) - necessary for `flake8` to be configured using a `pyproject.toml` file
    - [`radon`](https://radon.readthedocs.io/en/latest/intro.html) - a standalone tool for measuring [cyclomatic complexity](https://radon.readthedocs.io/en/latest/intro.html#cyclomatic-complexity).

      Radon out-of-the-box is a `flake8` plugin which enables VS Code and PyCharm to display red squiggly lines on functions whose complexity score is too high.
- [`black`](https://black.readthedocs.io/en/stable/) for formatting. Note that the line length is set to `119` for `black` and other tools that consider line length.
- [`pytest`](https://docs.pytest.org/en/8.2.x/) for unit testing since it is the industry standard testing framework
  - [`pytest-cov`](https://pytest-cov.readthedocs.io/en/latest/) for calculating coverage and displaying an HTML coverage report in the browser
- [`pre-commit` framework](https://pre-commit.com/) - a convenient, industry-standard way to install and run `flake8`, `pylint`, and the other tools all at once--and in isolated virtual environments. See `.pre-commit-config.yaml` for the configuration.
- `Makefile` - for running tasks, e.g. `make lint`, `make test`, `make install`.

  Make is unfortuanately a tool that
  comes pre-installed on most OSes, but it comes with its own scripting language which is limited and difficult to use compared to `bash`.
  It supports tab-based autocompletion when running commands and can be used to chain commands together, e.g. `make lint test build`.

  This template uses `Makefile` as a paper-thin wrapper over `run.sh` which allows you to author your tasks in `bash`, while
  still providing the convenience of tab-based autocompletion and chaining commands together.

  We are not in love with `Makefile` + `run.sh`, but it has advantages over alternative workflows such as

  - `bash` scripts are flexible. Most developers can quickly author simple bash scripts, especially with ChatGPT.
  - `Justfile` is *awesome*, but can be difficult to install in CI and most devs do not already have it installed.
  - `PyInvoke` is a thing, but requires an initial installation of `invoke` with Python, resulting in extra steps,
    e.g. installing in the system Python, or with `pipx`. It also has a slight learning curve over the first
    adding that much more friction to new developers joining projects.

  In summary, `Makefile` + `run.sh` is a decent solution for minimized learning curve (uses ubiquitous tools), easy setup,
  and performance (no slight hang when executing Python-based tasks).
