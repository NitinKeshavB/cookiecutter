# Python Package Cookiecutter

A [cookiecutter](https://cookiecutter.readthedocs.io/) template that scaffolds a
distributable Python package with linting, formatting, typing, testing, coverage,
packaging and release tasks already wired together — plus a
[Claude Code](https://claude.com/claude-code) agent harness so an AI coding agent is
productive in the new project from the first prompt.

## Quick start

```bash
# install cookiecutter into an isolated virtual environment
python -m venv ./venv/
source ./venv/bin/activate
pip install --upgrade pip
pip install cookiecutter

# generate a project, answering the prompts
cookiecutter https://github.com/NitinKeshavB/cookiecutter.git
```

Then, in the generated directory:

```bash
make install   # editable install with all dev extras
make test      # pytest + coverage
make lint      # black, isort, flake8, pylint, mypy, autoflake
```

### Prompts

| Prompt | Meaning | Example |
|---|---|---|
| `repo_name` | the directory name and the distribution (pip install) name | `my-awesome-package` |
| `package_import_name` | the importable module name | `my_awesome_package` |
| `harness_doctrine` | how much AI-agent doctrine to ship — `lean` or `full` | `lean` |

> **`package_import_name` must be a valid Python identifier** — lowercase, underscores,
> no hyphens. Nothing validates this yet, and a hyphenated value generates a package
> that cannot be imported (`import my-package` is a `SyntaxError`). See
> [Known limitations](#known-limitations).

## What you get

```
my-awesome-package/
├── src/my_awesome_package/
│   └── __init__.py            # the public API surface
├── tests/
│   ├── conftest.py            # puts tests/.. on sys.path; registers fixture plugins
│   ├── consts.py              # THIS_DIR, PROJECT_DIR
│   ├── unit_tests/            # mirrors the src/ module layout
│   └── fixtures/              # one module per fixture, registered in conftest.py
├── pyproject.toml             # metadata, dependencies, and all tool config
├── version.txt                # the single source of version truth
├── Makefile                   # thin wrapper over run.sh
├── run.sh                     # task implementations, in bash
├── .pre-commit-config.yaml    # the lint/format toolchain
├── CLAUDE.md                  # agent doctrine
├── .claude/                   # agent commands and skills
├── context/                   # the project's spec layer, pre-seeded
└── LOCAL-MEMORY/              # where agent analyses and plans are written
```

### Tasks in a generated project

| Command | Effect |
|---|---|
| `make install` | editable install with all dev extras |
| `make test` | pytest + coverage reports into `test-reports/` |
| `make test-quick` | as above, skipping tests marked `@pytest.mark.slow` |
| `make test-wheel-locally` | build a wheel, install it in a fresh venv, test the **installed** package |
| `make lint` | `pre-commit run --all-files` |
| `make build` | sdist + wheel into `dist/` |
| `make serve-coverage-report` | serve the HTML coverage report on `localhost:8000` |
| `make clean` | remove build, coverage and cache artifacts |
| `make publish-test` / `make publish-prod` | upload to TestPyPI / PyPI — **irreversible** |

## The AI agent harness

Generated projects ship an operational doctrine (`CLAUDE.md`), seven slash commands,
five skills, and a `context/` spec layer.

| Command | Use it for |
|---|---|
| `/qa` | run lint, tests and coverage, and triage what fails |
| `/explain <target>` | a cited mental model of how some code works |
| `/bug-why <error>` | root cause analysis — read-only, and requires a repro that fails first |
| `/bug-fix <analysis>` | the surgical fix, failing-test-first |
| `/howto-implement <feature>` | ranked approaches and testable acceptance criteria, before any code |
| `/implement <plan>` | execute the plan as a surgical change |
| `/verify [target]` | adversarially check a change, plan or diagnosis |

What makes this more than a prompt file:

- **`context/` ships pre-seeded.** Most agent harnesses leave their context layer as
  blank placeholders, which is the main reason they underperform. A generator already
  knows the layout, toolchain, task vocabulary and conventions — so
  `Project_Overview.md` and `Code_Patterns_Index.md` arrive populated with facts that
  are true of your project. Only the **domain glossary** starts empty, because only
  you know the domain; fill it early, it is the highest-leverage file in the repo.
- **The toolchain's real traps are written down**, because they are what an agent
  gets wrong here: docstrings are mandatory (`flake8-docstrings` enforces
  `D101`/`D102`/`D103` even though `pylint` disables its own check); `autoflake` runs
  `--remove-all-unused-imports` and will delete an `__init__.py` re-export nothing
  references; `mypy` runs with no `[tool.mypy]` table, so it catches less than it
  appears to; and the coverage floor is `0`, so a green test run says nothing about
  whether your change was covered.
- **`harness_doctrine` sizes the doctrine.** Skills and commands are lazily loaded —
  only their description frontmatter is resident — so the standing context cost is
  `CLAUDE.md` alone. `lean` (275 lines) carries evidence weights, named refuters,
  tier-based rigor, the checkpoint-before-code protocol, the surgical-change guard and
  the verification loop. `full` (354 lines) adds vocabulary locking, pattern reuse,
  repro kernels and reflexion lessons — gates that need a populated glossary and
  established patterns to act on, which a day-one package does not have.

Adapted from the Claude Code Agent Harness by Viacheslav Tronko (MIT); see
[`HARNESS-ATTRIBUTION.md`](./HARNESS-ATTRIBUTION.md) for provenance and deviations.

## Developing on this template

The repo has two layers, and confusing them is the most common mistake:

| Layer | Path | Rendered by Jinja? |
|---|---|---|
| **Generator** | repo root — `cookiecutter.json`, `run.sh`, `Makefile`, `tests/` | no |
| **Template** | `{{cookiecutter.repo_name}}/**` | **yes, every file, every generation** |

```bash
make install           # cookiecutter, pytest, pre-commit
make generate-project  # render into ./sample/ and git-init it
make test              # functional suite: generate, lint, build a wheel, test it
make lint              # repo-root hygiene + the Jinja safety scan
make clean             # remove sample/ and caches
```

`make test` is slow and hits the network — it builds a wheel in a throwaway venv and
tests the installed package. For a tight loop, use `make generate-project` and work
inside `sample/<name>/`.

### The Jinja contract

Cookiecutter renders **every file** under `{{cookiecutter.repo_name}}/`, so Jinja
delimiters are reserved characters there. `{{ cookiecutter.var }}` is intended; a
stray `{{`, `{%` or `{#` is a build break that fails every generation rather than
showing up as a local error. Single braces (`{slug}`) are plain text and safe.

This is enforced, not just documented:

```bash
python3 .claude/hooks/check_jinja_safety.py --scan
```

The same script runs as a Claude Code `PreToolUse` hook, so a non-compliant edit is
blocked before it lands, and again as a `pre-commit` hook, so CI fails on it. Two
escape hatches: add the path to `_copy_without_render` in `cookiecutter.json` when the
file needs no cookiecutter values at all (this is why `.claude/skills/*` is listed
there), or wrap the literal text in a Jinja raw block.

See [`CLAUDE.md`](./CLAUDE.md) for the full doctrine, including the register of known
defects.

## Opinions in this template

### File structure

- **`src/` layout.** The package is not importable from the repo root — only after
  `make install` does an editable install. That is deliberate: it stops tests passing
  against the working tree while the built package is broken.
- **`tests/unit_tests/` mirrors `src/`**, so the test for a module is findable by path.
- **`tests/conftest.py`** adds `tests/..` to `sys.path` so `from tests.x import y`
  works, and registers fixture modules via `pytest_plugins`. A fixture module that is
  not listed there is never discovered.
- **`version.txt` is the only source of version truth**; `pyproject.toml` reads it via
  `[tool.setuptools.dynamic]`.

### Tools

- [`setuptools`](https://setuptools.pypa.io/en/latest/userguide/index.html) for
  packaging — a `pip` + `venv` + `setuptools` workflow is the most officially
  supported, "vanilla" way to manage Python packages.
- [`black`](https://black.readthedocs.io/en/stable/) for formatting and
  [`isort`](https://pycqa.github.io/isort/) for imports. Line length is **119**.
- [`pylint`](https://pylint.readthedocs.io/en/stable/) and
  [`flake8`](https://flake8.pycqa.org/en/latest/) for linting, with these flake8 plugins:
  - [`flake8-docstrings`](https://pypi.org/project/flake8-docstrings/) — requires docstrings
  - [`flake8-pyproject`](https://pypi.org/project/Flake8-pyproject/) — lets flake8 read `pyproject.toml`
  - [`radon`](https://radon.readthedocs.io/en/latest/intro.html) — caps
    [cyclomatic complexity](https://radon.readthedocs.io/en/latest/intro.html#cyclomatic-complexity)
    at 10, and surfaces it as squiggly lines in VS Code and PyCharm
- [`mypy`](https://mypy-lang.org/) for type checking and
  [`autoflake`](https://github.com/PyCQA/autoflake) for dead imports.
- [`pytest`](https://docs.pytest.org/) with
  [`pytest-cov`](https://pytest-cov.readthedocs.io/en/latest/) for tests and coverage.
- [`pre-commit`](https://pre-commit.com/) to install and run all of the above in
  isolated environments, and to block direct commits to `main`.

### Why `Makefile` + `run.sh`

`Makefile` is a paper-thin wrapper: each target is one line that calls a `run.sh`
bash function. You author tasks in bash, but still get tab-completion and chaining
(`make lint test build`).

Make's own scripting language is limited and awkward compared to bash, but `make` is
preinstalled nearly everywhere. The alternatives each cost more than they give here:
[`just`](https://github.com/casey/just) is excellent but is another thing to install,
in CI as well as locally; [`invoke`](https://www.pyinvoke.org/) needs a Python
install step before any task can run, plus a learning curve. `Makefile` + `run.sh`
keeps the learning curve at zero and adds no startup latency.

## Known limitations

Verified, open, and tracked in [`CLAUDE.md`](./CLAUDE.md) §10 so they are not
rediscovered:

1. **`package_import_name` is not validated.** A hyphenated value generates a package
   that cannot be imported, and cookiecutter exits 0. A `pre_gen_project.py` hook
   would catch it.
2. **Generated projects ship no CI.** `.github/build-test-publish.yml` in the template
   is empty *and* misplaced — GitHub only reads `.github/workflows/`.
3. **`pylint` is pinned at `v2.16.3`, which cannot install on Python 3.12+** — its
   build imports `pkgutil.ImpImporter`, removed in 3.12 — so `make lint` fails for
   anyone on a modern interpreter. CI does not catch it because it pins Python 3.8.
4. **No `.vscode/` is shipped**, despite earlier versions of this README advertising
   recommended extensions and editor settings as a headline feature.
5. **Example test and fixture files are empty**, so a freshly generated project's
   `make test` collects nothing and its coverage number is meaningless.
6. **`requires-python = ">=3.7"`** is well past end-of-life and blocks modern syntax.
7. **`ruff` is configured in the root `pyproject.toml` but run by nothing.**

## License

The template is free to use. The agent harness is adapted from MIT-licensed work —
see [`HARNESS-ATTRIBUTION.md`](./HARNESS-ATTRIBUTION.md).
