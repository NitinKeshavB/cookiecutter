# Harness attribution and provenance

The agent harness in this repository — the operational-doctrine structure, the
skill/command split, the evidence-and-refuter discipline, the tier model and the
failure-mode registry — is **adapted from the Claude Code Agent Harness** by
Viacheslav Tronko, used under the MIT License.

| | |
|---|---|
| Upstream project | Claude Code Agent Harness |
| Author | Viacheslav Tronko (co-author: Olena Usova) |
| License | MIT |
| Reference fork consulted | `https://github.com/NitinKeshavB/claude_harness` |
| Pinned at commit | `8ce2129ec91c129b3c8e663d1a74a6d356f24866` |
| Relationship | **hard fork** — rewritten for Python packaging; upstream sync not maintained |

## Deviations from upstream

This is a deliberate hard fork, not a vendored copy. What changed and why:

1. **Rewritten for Python packaging.** Upstream is language-agnostic with
   `{YOUR_ORM}` / `{YOUR_UI_FRAMEWORK}` placeholders a human must fill. Here the
   doctrine and skills name this template's actual toolchain: `pytest`, `pip` +
   `setuptools`, the `black`/`isort`/`flake8`/`pylint`/`mypy`/`autoflake`
   pre-commit stack, and the `Makefile` → `run.sh` task runner.

2. **Frontend and enterprise scaffolding dropped.** No `F-XXX` frontend pattern
   class, no ORM/data-access layer placeholders, no Jira/Atlassian MCP assumptions.
   Issue references are GitHub-shaped.

3. **Skills consolidated 7 → 5.** Upstream's `requirements-analysis` is folded into
   `implementation-blueprint`, and `white-box-trace` into `task-verification`, whose
   Python equivalent is executing `pytest` with coverage rather than simulating
   control-flow traversal. Upstream's own CONTRIBUTING guidance prefers
   consolidation over duplicate skills.

4. **Two harnesses, not one.** The template repository and the projects it
   generates face different failure modes, so each has its own doctrine. The
   repo-root `CLAUDE.md` governs template work (Jinja safety, generator contract,
   verify-by-generating); `{{cookiecutter.repo_name}}/CLAUDE.md` governs generated
   projects.

5. **The context layer ships pre-seeded.** Upstream names its empty `context/`
   folder as its single biggest limitation. Because a generator already knows the
   package name, layout, toolchain and task vocabulary, those facts are written
   into `context/` at generation time instead of left as placeholders.

6. **Prose rules promoted to executed gates.** Upstream's gates are instructions a
   model may ignore. `.claude/hooks/check_jinja_safety.py` runs as a `PreToolUse`
   hook and blocks non-compliant edits outright, and runs again in `pre-commit`
   so CI enforces it too.

7. **Doctrine weight is a generation-time choice.** `harness_doctrine` (`lean` by
   default, `full` available) sizes the doctrine to the project, since a freshly
   generated package has no domain glossary or established patterns for upstream's
   heaviest gates to act on.

## Upstream license

```
MIT License

Copyright (c) 2026 Viacheslav Tronko

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

This notice is also carried into every generated project, so downstream users
inherit the attribution.
