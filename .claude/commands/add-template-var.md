---
description: "Add, rename, or remove a cookiecutter.json variable and update every consumer in the same change. Triggers: /add-template-var, \"add a cookiecutter prompt\", \"add a template variable\", \"rename repo_name\", \"make X configurable at generation time\", \"new cookiecutter option\"."
argument-hint: "<add|rename|remove> <variable_name> [default or new name]"
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# /add-template-var — change the generator contract safely

**Doctrine:** `CLAUDE.md` §5 (`cookiecutter.json` is a contract), §6 (Verification Loop).

`cookiecutter.json` is consumed by the template tree, by the test fixture, and by
`run.sh`. A one-sided edit leaves a literal `{{cookiecutter.x}}` in generated
output or breaks the whole test suite. Treat this as a cross-cutting change.

## 1. Validate input

`$ARGUMENTS` empty ⇒ reply with the usage line and STOP. A variable name must be
`snake_case`; cookiecutter treats a leading `_` as private (never prompted), which
is a deliberate choice, not a default.

## 2. Map every consumer first — read before writing (P0 #1)

```bash
grep -rn 'cookiecutter\.<var>' . --include='*' | grep -v '^./sample/'
grep -rn '<var>' cookiecutter.json tests/ run.sh
```

List the hits explicitly in your Checkpoint. Four places matter and the third is
the one that gets forgotten:

1. `cookiecutter.json` — the declaration.
2. `{{cookiecutter.repo_name}}/**` — template consumers.
3. **`tests/fixtures/project_dir.py`** — hardcodes the generation context. A new
   variable with **no default** breaks every functional test, because the fixture
   passes only `repo_name` and `package_import_name`.
4. `run.sh` — `open-pr-with-generated-project` writes its own config file with a
   fixed `default_context`; a required variable breaks that path too.

## 3. Choose the variable shape

| Shape | JSON | Use when |
|---|---|---|
| Free text | `"var": "default"` | names, descriptions, emails |
| Choice | `"var": ["first", "second"]` | a closed set — **first entry is the default** under `--no-input` |
| Boolean | `"var": "yes"` as a choice `["yes","no"]` | feature flags; cookiecutter has no real bool |
| Private | `"_var": ...` | config, never prompted (e.g. `_copy_without_render`) |

**Always give a usable default.** It is what `--no-input` and the test suite rely on.

## 4. Apply, in one commit

Declaration and every consumer together. Conditional *content* belongs in a Jinja
`{% if %}` block inside the file; conditional *file existence* needs a
`hooks/post_gen_project.py`, which is a bigger change — flag it rather than
improvising one.

## 5. Verify — mandatory

```bash
python3 .claude/hooks/check_jinja_safety.py --scan
make clean && make generate-project
grep -rn 'cookiecutter' sample/        # must return nothing
make test
```

The grep is the specific check for this command: it is the only thing that catches
a consumer you missed. `make test` confirms the fixture still generates.

Removing or renaming a variable is a **breaking change** for anyone re-running the
template against an existing project — say so explicitly in your summary.

End with: `In one sentence: <action> '<var>'; consumers updated = <N>; render = <PASS/FAIL>; make test = <PASS/FAIL/NOT RUN>.`
