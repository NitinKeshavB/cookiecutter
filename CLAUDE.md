# CLAUDE.md — Operational Doctrine (cookiecutter template repo)

**Authority:** SYSTEM > this file > code. Override only by explicit user intent.
**Read order:** this file → `cookiecutter.json` → the template tree → the test suite.
**Tagline:** Rules guide. Tools do. Evidence decides.

> This doctrine governs work on **the template itself**. The harness shipped
> *into* generated projects is a different artifact with a different doctrine —
> see `{{cookiecutter.repo_name}}/CLAUDE.md`. Do not conflate the two.

---

## 1. Mission

This repo is a [cookiecutter](https://cookiecutter.readthedocs.io/) template that
scaffolds opinionated Python packages. You are working on a **code generator**,
not an application. Every edit you make is multiplied across every project
generated from it, and a mistake here is invisible until someone else's
generation fails.

**Core directive:** a change to the template is not done when it looks right.
It is done when a project generated from it lints and tests clean.

---

## 2. The two layers — never confuse them

| | Path | Rendered by Jinja? | Audience |
|---|---|---|---|
| **Generator** | repo root: `cookiecutter.json`, `run.sh`, `Makefile`, `tests/`, `.claude/`, `CLAUDE.md` | No | people working on the template |
| **Template** | `{{cookiecutter.repo_name}}/**` | **Yes** — every file, every generation | people using generated projects |

Before any edit, state which layer you are in. A fix applied to the wrong layer
is the most common failure in this repo: editing `Makefile` when the bug is in
`{{cookiecutter.repo_name}}/Makefile` changes nothing for users, and vice versa.

---

## 3. P0 Hard Constraints — NEVER VIOLATE

| # | Rule |
|---|------|
| 1 | **READ before EDIT.** Before modifying file X, `Read` file X this turn. Quote `file:line` when referencing it. Never edit from memory. |
| 2 | **DECLARE THE LAYER.** Name generator-vs-template (§2) before editing. If a change belongs in both, change both in the same commit. |
| 3 | **JINJA CONTRACT (§4).** Everything under `{{cookiecutter.repo_name}}/` is a Jinja template. Treat stray `{{`, `{%`, `{#` as a build break, not a typo. |
| 4 | **COOKIECUTTER.JSON IS THE CONTRACT (§5).** Adding, renaming or removing a variable is a breaking change to every template file that references it. Never do it one-sided. |
| 5 | **VERIFY BY GENERATING (§6).** "The template looks correct" is not evidence. Render it and run the generated project's own checks. |
| 6 | **SURGICAL CHANGES.** Every changed line traces to the request. Do not reformat untouched code, reorder imports, or "modernize" working config. Match the existing style even where you would do it differently. |
| 7 | **NO TODOs / NO PLACEHOLDERS.** Generated projects inherit every placeholder you leave behind. Code is complete or omitted. |
| 8 | **ABSTAIN AND PUSH BACK.** Below MEDIUM confidence, ask. Surface inconsistencies; never run along with a wrong assumption silently. Never present a guess as a fact. |
| 9 | **FALSIFIABILITY.** Every HIGH+ confidence claim names a **Refuter** — the concrete file, command or test output that would force you to retract it. No refuter ⇒ downgrade to MEDIUM. |
| 10 | **EMPIRICAL > IMAGINED.** A command you ran beats reasoning about what a command would print. Paste the transcript. |
| 11 | **NO REWARD HACKING.** Never weaken a test, lower `MINIMUM_TEST_COVERAGE_PERCENT`, or add a lint ignore to make a check pass. Fix the cause or report the blocker. |
| 12 | **SHARED STATE NEEDS CONSENT.** Do not touch `.github/workflows/`, `.gitignore`, `version.txt`, secrets, or the `gh`-driven functions in `run.sh` without explicit approval. They act outside this working tree. |

---

## 4. The Jinja contract — the defining hazard of this repo

Cookiecutter renders **every file** under `{{cookiecutter.repo_name}}/` through
Jinja2, including dotfiles, Markdown, JSON and YAML. Jinja delimiters are
therefore reserved characters in that subtree.

| Delimiter | Meaning to Jinja | Verdict |
|---|---|---|
| `{{ cookiecutter.var }}` | variable read | **intended** — this is the point |
| `{% if %}` / `{% raw %}` / `{% for %}` | control tag | allowed, deliberate use only |
| `{{` not reading `cookiecutter.` | expression opener | **build break** |
| `{#` | comment opener | **build break** unless closed by `#}` |
| `{slug}`, `{ext}`, `${VAR}` | nothing — plain text | safe, passes through |

**This is not hypothetical.** The vendored harness shipped a literal `{#term-slug}`
in prose. `{#` opens a Jinja comment; with no `#}` the renderer aborts every
generation with `TemplateSyntaxError: Missing end of comment tag`.

**Two escape hatches, in order of preference:**

1. **`_copy_without_render`** in `cookiecutter.json` — the file is copied byte-for-byte
   and Jinja never sees it. Correct for generic content that needs no cookiecutter
   values (this is why `.claude/skills/*` is listed there).
2. **A Jinja raw block** around the literal text — correct when the file *does* need
   cookiecutter values elsewhere.

**Enforcement, not etiquette.** `.claude/hooks/check_jinja_safety.py` runs as a
`PreToolUse` hook and **blocks** any Write/Edit that would introduce a hazard into
a rendered path. It reads `_copy_without_render` from `cookiecutter.json`, so it
stays consistent with the real config. Audit the whole tree any time:

```bash
python3 .claude/hooks/check_jinja_safety.py --scan
```

A blocked edit is the hook doing its job. Fix the content — do not route around
the hook, and do not add a path to `_copy_without_render` merely to silence it.

---

## 5. `cookiecutter.json` is a contract

| Variable | Role |
|---|---|
| `repo_name` | names the generated directory, the distribution name, and the template dir itself |
| `package_import_name` | names `src/<pkg>/` and every `import` in generated code |
| `harness_doctrine` | `lean` (default) or `full` — selects how much agent doctrine ships into the generated project |
| `_copy_without_render` | paths exempt from Jinja (§4) |

**Changing a variable is a cross-cutting change.** Before you touch it:

1. `grep -rn 'cookiecutter\.<var>' '{{cookiecutter.repo_name}}/'` — find every consumer.
2. Update the variable and every consumer in the same commit.
3. Check `tests/fixtures/project_dir.py:21-24`, which hardcodes the context the
   test suite generates with. A newly **required** variable with no default
   breaks every test.
4. Re-render and verify (§6).

The `/add-template-var` command walks this.

---

## 6. Verification Loop — the single highest-leverage rule

Reading the template proves nothing. The only evidence that counts is a
generated project passing its own checks.

```bash
make generate-project    # render into ./sample/ and git-init it
make test                # functional tests: generate, lint, build a wheel, test it
```

What `make test` actually does (`tests/fixtures/project_dir.py`): cookie-cuts a
uniquely-named project into `sample/`, `git init`s it, runs `make lint-ci` on it,
then `test__makefile.py` runs `make install` and `make test-wheel-locally` —
which builds a wheel in a throwaway venv and tests the *installed* package.

**It is slow and it touches the network** (pip installs into a fresh venv). Budget
minutes, not seconds. Do not skip it on template changes and do not substitute a
faster proxy for it. For a tight loop while iterating, `make generate-project`
then run commands inside `sample/<name>/` by hand — but the functional suite is
the gate.

**Three tiers. Use the cheapest one that covers the change, and say which you ran.**

| Tier | Command | Cost | What it does |
|---|---|---|---|
| fast | `make test-fast` | ~1s, no network | renders in-process, asserts the output tree, placeholders, contract and Jinja safety |
| quick | `make test-quick` | ~1s | everything not marked `slow` |
| full | `make test` | minutes, network | adds the functional suite: generate, `git init`, `make lint-ci`, `make install`, build a wheel in a throwaway venv and test the installed package |

`make test-fast` is the loop to use while editing. It catches what actually
goes wrong in a template -- an unrendered placeholder, a file that stopped
being copied, a Jinja conditional emitting the wrong branch -- without building
anything.

**Tier the evidence to the blast radius:**

| Change | Required evidence |
|---|---|
| Prose in a repo-root `.md` | read the file; no generation needed |
| Any file under `{{cookiecutter.repo_name}}/` | `make test-fast` |
| `cookiecutter.json`, `hooks/`, or a template `pyproject.toml`/`run.sh`/`Makefile` | full `make test` transcript pasted |
| `.pre-commit-config.yaml` pins, CI workflow, `version.txt`, release plumbing | full `make test` **and** explicit user approval (P0 #12) |

If you cannot execute the loop this session, say so plainly: cite the exact
command, the expected output, and why it could not run. "Should work" is not
verification.

---

## 7. Checkpoint — first visible block on any non-trivial change

Reasoning before conclusions. Trivial lookups and single reads skip this.

```markdown
**CHECKPOINT**
**Layer:** generator | template (§2)
**Intent:** <what the user asked, restated>
**Read:** cookiecutter.json:1-6, {{cookiecutter.repo_name}}/run.sh:40 (quoted)
**Jinja impact:** none | rendered path — scan required
**Contract impact:** none | cookiecutter.json variable touched — §5 steps
**Plan:** <2-5 steps>
**Confidence:** HIGH — **Refuter:** if `make generate-project` fails, the plan is wrong.
**Verification:** <the exact command that will prove this>
```

Invalid if: code appears before reasoning, the layer is unstated, or confidence
is HIGH+ with no refuter.

---

## 8. Repo map

```
cookiecutter/
  cookiecutter.json          <- the contract (§5)
  CLAUDE.md                  <- this file
  hooks/
    pre_gen_project.py       <- validates the answers before any file is written
  .claude/
    settings.json            <- permissions + the PreToolUse Jinja hook
    hooks/
      check_jinja_safety.py  <- §4 enforcement; also `--scan`
    commands/                <- /verify-template, /add-template-var, /jinja-audit
  Makefile                   <- thin wrapper over run.sh
  run.sh                     <- task implementations (bash)
  .pre-commit-config.yaml    <- repo-root hygiene; excludes the template tree
  version.txt                <- CI tags the repo with this on push to main
  tests/
    conftest.py              <- registers the fixture plugins
    consts.py                <- PROJECT_DIR
    utils/project.py         <- generate_project(), initialize_git_repo()
    fixtures/
      rendered_project.py    <- FAST: in-process render, no git/pip/network
      project_dir.py         <- SLOW: subprocess render + git init + lint
    unit_tests/              <- the fast tier (§6)
    functional_tests/        <- the slow tier, all marked `slow`
  .github/workflows/
    build-pipeline.yml       <- check-version-txt, lint, tests, push-tags
  {{cookiecutter.repo_name}}/   <- THE TEMPLATE (everything below is rendered)
    CLAUDE.md                <- generated project's doctrine (lean|full)
    .claude/                 <- settings, commands, skills (skills copied verbatim)
    context/                 <- spec layer, pre-seeded with real project facts
    LOCAL-MEMORY/            <- agent artifact output root
    src/{{cookiecutter.package_import_name}}/
    tests/
    .github/workflows/       <- CI shipped into generated projects
    pyproject.toml, Makefile, run.sh, .pre-commit-config.yaml, version.txt
```

Generated output lands in `sample/` and is gitignored. `make clean` removes it
along with caches and `tests/cookiecutter*json` scratch config.

---

## 9. Tasks

`Makefile` targets are one-line wrappers over `run.sh` functions; add real logic
to `run.sh` and expose it in the `Makefile`.

| Target | `run.sh` function | Effect |
|---|---|---|
| `make install` | `install` | pip install cookiecutter, pytest, pre-commit |
| `make generate-project` | `generate-project` | render into `sample/`, git init, commit |
| `make lint` | `lint` | `pre-commit run --all-files` |
| `make lint-ci` | `lint:ci` | same, with `no-commit-to-branch` skipped |
| `make test-fast` | `test:fast` | `pytest tests/unit_tests/` — the fast tier (§6) |
| `make test-quick` | `test:quick` | everything not marked `slow` |
| `make test` | `run-tests` | `pytest tests/` — the whole suite, including the slow tier |
| `make clean` | `clean` | remove `sample/`, caches, build artifacts |
| `make help` | `help` | list every `run.sh` function |

`run.sh` also holds `gh`-driven repo provisioning (`create-repo-if-not-exists`,
`configure-repo`, `open-pr-with-generated-project`, `create-sample-repo`). These
create repos, set secrets and push branches. **They act outside this working
tree — P0 #12 applies; never run them unprompted.**

---

## 10. Known defects — do not rediscover, do not silently "fix"

Each is real and verified. Fix on request, in its own commit. `README.md`
carries the same list for users. **Keep the two in sync** — a defect register
that disagrees with itself is worse than none.

1. **`.vscode/` is absent.** Earlier versions of `README.md` advertised
   `.vscode/extensions.json` and `.vscode/settings.json` as a headline feature.
   No such directory exists anywhere in the repo, so no generated project gets
   one. The README claim is gone; shipping the directory is still open, and it
   would be a genuine quality-of-life win given the toolchain expects editor
   integration (`radon` surfacing complexity as squiggles, `black` on save).
2. **Example test and fixture files are empty.**
   `{{cookiecutter.repo_name}}/tests/unit_tests/example_test.py` and
   `tests/fixtures/example_fixture.py` are zero bytes, so a fresh project's
   `make test` collects nothing and its coverage number is meaningless
   (`MINIMUM_TEST_COVERAGE_PERCENT=0` hides it). A single real passing test and
   one real fixture would make `make test` mean something on day one.
3. **`requires-python = ">=3.7"`** is well past end-of-life. It blocks modern
   syntax in generated packages for no benefit, and the shipped CI matrix does
   not test 3.7 or 3.8 because those runtimes are unavailable — so the declared
   floor is aspirational. Raising it is a breaking change for consumers of an
   already-published generated package, so it is a deliberate decision.
4. **`ruff` is configured but run by nothing.** The repo-root `pyproject.toml`
   carries `[tool.ruff]` and `[tool.ruff.per-file-ignores]`, but no hook or task
   invokes `ruff` in either layer. Either wire it up or drop the config — dead
   configuration misleads readers and agents alike. Consolidating generated
   projects onto `ruff` would also cut their seven pre-commit hook environments
   to two or three; that was considered and deliberately deferred.
5. **`generate-project` assumes a clean `sample/`.** `run.sh` does
   `cd "$THIS_DIR/sample"; cd $(ls)`, which breaks if `sample/` already holds
   more than one entry. Run `make clean` first.
6. **The template README has an empty heading.**
   `{{cookiecutter.repo_name}}/README.md` has a bare `###` above the
   clone-and-install block. It needs a title; the content below suggests
   "Getting started". Left alone because naming it is a content decision, not a
   mechanical fix.

**Fixed, recorded so the history is legible:** generated projects shipped no CI
(the workflow file was empty and misplaced); `package_import_name` was
unvalidated, so a hyphenated answer produced an unimportable package with a
zero exit code; `pylint` was pinned at a revision that cannot install on Python
3.12+, which broke `make lint` for anyone on a modern interpreter; the repo-root
`.pre-commit-config.yaml` was an empty file, so `lint:ci` could never run;
`run.sh run-tests` quoted `"${@:-...}"` wrongly, so `test:quick` always exited 4;
and `tests/utils/project.py` renamed an unborn git branch, which only git >= 2.30
accepts, so the whole functional tier errored at fixture setup on older git.

---

## 11. Pre-send checklist

1. Layer declared (§2) and correct.
2. `--scan` clean if any rendered path changed (§4).
3. `cookiecutter.json` consumers updated in the same commit if the contract changed (§5).
4. Verification Loop run at the tier §6 requires; transcript pasted, or non-execution
   explained with the exact command.
5. Every changed line traces to the request; no orthogonal reformatting (P0 #6).
6. No placeholder or TODO left in template content (P0 #7).
7. Confidence stated; refuter named for HIGH+ (P0 #9).
8. Claims of "ran" / "read" / "tested" are backed by an actual tool result this turn.
9. Shared-state files untouched without approval (P0 #12).
10. Close with `In one sentence: <what was delivered>.`

---

## 12. Attribution

The doctrine, skill and command structure here is adapted from the
**Claude Code Agent Harness** by Viacheslav Tronko (MIT). This repo is a hard
fork rewritten for Python packaging; upstream sync is not maintained. Full
provenance and the list of deviations: `HARNESS-ATTRIBUTION.md`.

**Rules guide. Tools do. Evidence decides.**
