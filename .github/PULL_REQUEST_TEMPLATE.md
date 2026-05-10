<!--
Thanks for the PR! Keep this concise — the diff already shows WHAT changed.
This template asks for WHY + risk areas + how-to-verify.
-->

## Why

<!-- One paragraph: motivation, problem solved, or feature delivered. -->

## What changed

<!-- Bullet list of meaningful changes (not every file). -->

- 
- 

## Test plan

<!-- Concrete commands a reviewer can run to verify. -->

```bash
pytest tests/
# pyflakes lovarch_cli tests (excluding squad/)
find lovarch_cli tests -type d -name squad -prune -o -name '*.py' -print | xargs pyflakes
# Manual smoke
lovarch --version
lovarch info
```

## Risk areas

<!-- Anything reviewers should look at carefully? Breaking changes? Migration steps? -->

- [ ] Breaking change to CLI interface (subcommand removed, flag renamed)?
- [ ] Affects state in `~/.lovarch/` (projects/cache/credentials)?
- [ ] Touches the squad payload (`lovarch_cli/squad/`)? (it shouldn't — see CONTRIBUTING.md)
- [ ] Adds a new dependency? (pyproject.toml + rationale)
- [ ] Affects i18n? (all 4 languages updated?)

## Linked issues

<!-- Closes #N, Refs #M -->

## Reviewer checklist

- [ ] CI green (pytest matrix 3.11/3.12/3.13 + pyflakes + smoke)
- [ ] Conventional commit prefix (`feat:`, `fix:`, `refactor:`, etc.)
- [ ] CHANGELOG.md updated under `[Unreleased]` if user-visible
- [ ] Docs updated if behavior changed (README, docs/)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
