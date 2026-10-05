---
description: "Run the real verification loop for this cookiecutter template: Jinja-safety scan, render a project, and run the functional suite that lints it and tests an installed wheel. Triggers: /verify-template, \"verify the template\", \"does the template still generate\", \"did I break generation\", \"test the cookiecutter\", before committing any change under the template directory."
argument-hint: "[--scan-only | --render-only | --full]"
allowed-tools: Read, Glob, Grep, Bash
---

# /verify-template — prove a generated project still works

**Doctrine:** `CLAUDE.md` §6 (Verification Loop), §4 (Jinja contract).
**Modes:** `--scan-only` (seconds) · `--render-only` (fast loop) · `--full` (the gate; default when a rendered path changed).

## 0. Hard gate

"It's only a docs change", "the diff is tiny", "I'm confident it renders" do NOT
substitute for evidence. Reading the template proves nothing — only a rendered
project passing its own checks does (P0 #5).

This command is **read-only with respect to the template**. It writes only to
`sample/` and test scratch paths. Never edit template files to make a stage pass;
report the failure instead (P0 #11).

## 1. Stage 1 — Jinja safety (always)

```bash
python3 .claude/hooks/check_jinja_safety.py --scan
```

Non-zero exit ⇒ **STOP**. Report each hazard with its path and fix it per §4
before going further; a hazard here means every generation is already broken.
Stop after this stage on `--scan-only`.

## 2. Stage 2 — render (always)

```bash
make clean && make generate-project
```

`make clean` first: `run.sh generate-project` does `cd $(ls)` inside `sample/`
and breaks on a dirty directory (known defect #4).

Then inspect the output, don't assume it:

- `ls -la sample/*/` — is the tree complete?
- Did `src/<package_import_name>/` get the right name?
- `grep -rn 'cookiecutter' sample/` — **any hit is an unrendered placeholder**, which
  means a variable is misspelled or the path is wrongly in `_copy_without_render`.
- Confirm `.claude/skills/` arrived verbatim and `context/` arrived rendered.

Stop after this stage on `--render-only`.

## 3. Stage 3 — functional suite (`--full`, the gate)

```bash
make test
```

This generates its own project, `git init`s it, runs `make lint-ci` on it, then
`make install` and `make test-wheel-locally` — building a wheel in a throwaway
venv and testing the installed package. **Slow and network-dependent** (pip into
a fresh venv). Budget minutes; do not abandon it midway and call the result unknown.

On failure, localise before fixing: a `make lint-ci` failure is a template content
problem (pre-commit rewrote a generated file); a `test-wheel-locally` failure is a
packaging problem in the template `pyproject.toml`.

## 4. Report

Paste the real transcript tail of each stage you ran — never a summary of what
you expect it to say (P0 #10).

| Stage | Command | Verdict |
|---|---|---|
| Jinja safety | `--scan` | PASS / FAIL + hazards |
| Render | `make generate-project` | PASS / FAIL + unrendered placeholders |
| Functional | `make test` | PASS / FAIL / NOT RUN + reason |

If any stage was not run, say which and why. A partial run is a partial verdict —
label it as such rather than implying the gate passed.

End with: `In one sentence: verified the template at <modes>; verdict = <X>.`
