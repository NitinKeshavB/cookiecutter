# {{cookiecutter.repo_name}}

## Quick start

```bash
pip install {{cookiecutter.repo_name}}
```

```python
from {{cookiecutter.package_import_name}} import ...
```

## Developing/Contributing

### System requirements

You will need the following installed on your machine to develop on this codebase

- `make` AKA `cmake`, e.g. `sudo apt-get update -y; sudo apt-get install cmake -y`
- Python 3.7+, ideally using `pyenv` to easily change between Python versions
- `git`

###

```bash
# clone the repo
git clone https://github.com/<your github username>/{{cookiecutter.repo_name}}.git

# install the dev dependencies
make install

# run the tests
make test
```

## AI agent harness

This project ships a [Claude Code](https://claude.com/claude-code) harness: a set of
rules, slash commands and skills that make an AI coding agent investigate before it
acts, cite `file:line` for every claim, keep changes surgical, and prove a change by
running something rather than by asserting it works.

| Path | Purpose |
|---|---|
| `CLAUDE.md` | the operational doctrine — read first |
| `.claude/commands/` | slash commands |
| `.claude/skills/` | the operational loops the commands invoke |
| `context/` | this project's spec layer — **fill in the glossary** |
| `LOCAL-MEMORY/` | where analyses and plans are written |

### Commands

| Command | Use it for |
|---|---|
| `/qa` | run lint, tests and coverage, and triage what fails |
| `/explain <target>` | a cited mental model of how some code works |
| `/bug-why <error>` | root cause analysis — read-only, requires a repro that fails |
| `/bug-fix <analysis>` | the surgical fix, failing-test-first |
| `/howto-implement <feature>` | ranked approaches and testable acceptance criteria, before any code |
| `/implement <plan>` | execute the plan as a surgical change |
| `/verify [target]` | adversarially check a change, plan or diagnosis |

Most work needs two: one to analyse, one to execute. `/qa` and `/verify` are the
guard rails around them.

### Getting the most out of it

**Fill in `context/02_Domain_Knowledge/Domain_Glossary.md` early.** It is the
highest-leverage file in the repo and it starts empty. One agreed name per concept,
with the synonyms to avoid, is what stops the same idea becoming four different names
across four modules — cheap now, expensive to retrofit later.

Then keep `context/01_Solution_Overview/Project_Overview.md` honest as the package
grows. Its layout and toolchain sections were pre-filled at generation time and are
accurate today.

The doctrine was generated at the `{{cookiecutter.harness_doctrine}}` weight. The
`lean` doctrine covers the core: evidence, refuters, surgical changes and the
verification loop. The `full` doctrine adds vocabulary locking, pattern reuse, repro
kernels and reflexion lessons — worth adopting once the project has real domain terms
and established patterns. Regenerating with `harness_doctrine=full` shows the
additional sections.

Adapted from the Claude Code Agent Harness by Viacheslav Tronko (MIT) — see
`HARNESS-ATTRIBUTION.md`.
