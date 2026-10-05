---
description: "Audit the cookiecutter template tree for Jinja rendering hazards (stray expression openers, unknown tags, unclosed comment delimiters) and explain each fix. Triggers: /jinja-audit, \"scan for jinja problems\", \"why did generation fail\", \"TemplateSyntaxError\", \"Missing end of comment tag\", \"unrendered placeholder in the output\", after vendoring any third-party content into the template."
argument-hint: "[path under the template dir]"
allowed-tools: Read, Glob, Grep, Bash
---

# /jinja-audit — find Jinja hazards before users do

**Doctrine:** `CLAUDE.md` §4 (Jinja contract).

## 1. Scan

```bash
python3 .claude/hooks/check_jinja_safety.py --scan
```

Scope to `$ARGUMENTS` when given, otherwise the whole template tree. The scanner
reads `_copy_without_render` from `cookiecutter.json`, so its exempt count should
match what that key covers — if it does not, the config and your mental model have
diverged; reconcile that first.

## 2. Classify every hazard before fixing it

| Hazard | Cause | Correct fix |
|---|---|---|
| Unclosed `{#` | literal text like `{#slug}` in prose | raw-wrap it, or exempt the file |
| `{{` not reading `cookiecutter.` | a code sample or another templating language | raw-wrap the sample |
| Unknown `{%` tag | an unsupported or misspelled Jinja tag | correct the tag, or raw-wrap |
| Unrendered `cookiecutter.` in output | file wrongly in `_copy_without_render`, or a typo'd variable | fix the glob or the name |

**Choose the escape hatch deliberately** (§4): `_copy_without_render` for files that
need no cookiecutter values at all — it is the robust option because Jinja never
touches the file; a raw block for files that need values elsewhere.

**Never add a path to `_copy_without_render` just to clear a finding.** If the file
genuinely needs a cookiecutter variable, exempting it silently ships a literal
`{{cookiecutter.x}}` into every generated project — a worse bug than the one you
cleared, and one the scanner cannot see. Verify that distinction by grepping the
file for `cookiecutter.` before you exempt it.

## 3. Prove the fix

A clean scan is necessary, not sufficient — it does not prove the file still
renders with the *right* values. Finish with:

```bash
make clean && make generate-project
grep -rn 'cookiecutter' sample/    # must return nothing
```

End with: `In one sentence: audited <scope>; <N> hazards; <N> fixed; render = <PASS/FAIL>.`
