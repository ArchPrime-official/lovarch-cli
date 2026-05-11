# Agent development — continuous improvement loop

> Status: Active since 2026-05-11. Required reading before editing the squad.

This doc describes the **end-to-end workflow** for improving the squad
architettura-progetto agents, tasks, workflows, templates, and pipeline
logic — from a one-line prompt tweak to shipping the change to all
brew-installed users.

## Mental model: three environments

The squad payload exists in three places at the same time. Each has a
purpose, and editing the wrong one wastes work.

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. DEV       — where you edit (source-of-truth)                    │
│     /Users/pablo/Lovarch/squads/architettura-progetto/              │
│                                                                     │
│     One-shot edits, iterations, experiments. ALL agent changes      │
│     start here.                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │  promote (when satisfied):
                              │  lovarch dev refresh-squad
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. STAGED    — committed snapshot in this repo                     │
│     /Users/pablo/lovarch-cli/lovarch_cli/squad/                     │
│                                                                     │
│     Vendored copy reviewed via PR, committed to git, NOT yet        │
│     released. This is what the next `git tag v0.1.X` will ship.    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │  release:
                              │  git tag v0.1.X && git push
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. PRODUCTION — what brew-installed users run                      │
│     /opt/homebrew/Cellar/lovarch-cli/0.1.X/.../squad/               │
│                                                                     │
│     Read-only on each user's machine. Updated via `brew upgrade`    │
│     when they pull the next release.                                │
└─────────────────────────────────────────────────────────────────────┘
```

**The cardinal rule:** edit only in DEV. Anything you change in STAGED
gets wiped on the next `lovarch dev refresh-squad`. Anything you change
in PRODUCTION gets wiped on `brew upgrade`.

## One-time setup

Add this to your `~/.zshrc` (or `~/.bashrc`):

```bash
export LOVARCH_SQUAD_SRC="$HOME/Lovarch/squads/architettura-progetto"
```

Then `source ~/.zshrc`. Verify:

```bash
lovarch dev show-squad-root
# Should show:
#   Resolved path:   ...architettura-progetto
#   Source:          override ($LOVARCH_SQUAD_SRC)
```

If your monorepo lives elsewhere, adjust the path. With the env var set,
every `lovarch run` reads from your DEV path instead of the bundled
vendor — zero refresh needed for iteration.

## Daily iteration loop

```bash
# 1. Edit DEV (any agent prompt, task, template, workflow YAML, or
#    pipeline_runner.py — all live here)
$EDITOR ~/Lovarch/squads/architettura-progetto/agents/concept-designer.md

# 2. Test the change immediately — uses $LOVARCH_SQUAD_SRC automatically
lovarch run my-test-project --skip-audit --dry-run

# 3. Iterate. The CLI prints a "↳ squad: <path> (override)" line so you
#    know you're in dev mode.
```

For a **Premium real-run** during dev (gasta créditos):

```bash
lovarch run my-test-project   # without --dry-run
```

To bypass the env var for one command (test as production user would):

```bash
unset LOVARCH_SQUAD_SRC && lovarch run my-test-project
# OR override per-invocation:
lovarch run my-test-project --squad-src /path/to/other/squad
```

## What lives where (editable surfaces)

In `~/Lovarch/squads/architettura-progetto/`:

| Path | What | When to edit |
|---|---|---|
| `agents/*.md` (17) | Per-agent prompt + Voice DNA + heuristics + Veto conditions | Tweaking output style, fixing factual mistakes, adding examples |
| `tasks/*.md` (6) | Executable tasks (audit-input, generate-cad-plan, etc) | Adding inputs/outputs, refining pre/post conditions |
| `workflows/dal-brief-al-cantiere.yaml` | Sequence of agents + gates | Reordering, adding parallel phases, adding QA gates |
| `templates/*.md` (4) | CILA/SCIA, capitolato, contratto, asseverazione skeletons | Updating to new normativa, fixing legal phrasing |
| `scripts/pipeline_runner.py` (1821 LoC) | Python orchestration: API calls, retries, persistence | Bug fixes, performance, new resilience patterns |
| `data/prezzario-lombardia-sample.json` | Reference pricing | Annual price updates |
| `config.yaml` | Squad metadata | New agent registration |

**Excluded from vendor (live in DEV only):**

- `data/sample-input/` and `data/sample-input-villa-chianti/` (~49MB of
  photos / DXF / PDF). Heavy assets ship via GitHub Releases. See
  [squad-vendoring.md](./squad-vendoring.md).

## Promoting DEV → STAGED (before release)

When you've validated a batch of dev changes and want to release them:

```bash
cd ~/lovarch-cli

# Optional dry-run preview
lovarch dev refresh-squad --dry-run

# Apply
lovarch dev refresh-squad

# Review what changed
git diff --stat lovarch_cli/squad/

# Commit (logical chunks, not all-at-once if multiple themes)
git add lovarch_cli/squad/
git commit -m "feat(squad): improve concept-designer prompt + add 3 examples"
git push -u origin feat/squad-improvements
gh pr create --fill
```

The dev command auto-detects the target (`lovarch_cli/squad/` inside
the cloned repo when running from an editable install). For non-default
layouts pass `--source` and/or `--target` explicitly.

## STAGED → PRODUCTION (cutting a release)

After the squad-improvements PR is merged:

```bash
cd ~/lovarch-cli
git checkout main && git pull

# Bump version
$EDITOR lovarch_cli/version.py    # e.g. "0.1.1" → "0.1.2"

# Update CHANGELOG
$EDITOR CHANGELOG.md
# Move [Unreleased] items to [0.1.2]

git commit -am "chore: bump v0.1.2"
git tag v0.1.2
git push origin main v0.1.2
```

What happens next is automated by `.github/workflows/`:

1. **`attach-to-release.yml`** — builds wheel + sdist, creates GitHub
   Release v0.1.2 with artifacts attached.
2. **`bump-homebrew-formula.yml`** — opens a PR on
   `ArchPrime-official/homebrew-lovarch` with the new SHA256.
3. You merge the homebrew PR → `brew upgrade lovarch-cli` lands the
   change for every installed user.

See [release-process.md](./release-process.md) for the full release flow.

## Cadence guide

| Change type | Version bump | Frequency |
|---|---|---|
| Single-agent prompt tweak | PATCH (v0.1.X) | Weekly during the course |
| New agent or new command | MINOR (v0.X.0) | Per sprint (4-6 weeks) |
| Breaking CLI API change | MAJOR (v1.0.0) | Rare — declares stability promise |

Pre-release tags (`v0.1.2-beta.1`) attach to the GitHub Release as
pre-release and skip the homebrew bump — useful when you want testers
to try a change without auto-rolling it to everyone.

## Testing prompt changes without running the full pipeline

A full `lovarch run` against Premium costs ~$1.20 / 3500 credits and
takes ~14 min. For prompt iteration, use Free dry-run:

```bash
lovarch run my-test-project --skip-audit --dry-run
```

This invokes the pipeline runner in simulation mode — agents are not
called, but the input is read, the workflow YAML is parsed, and the
output structure is sketched. Good for catching:

- Workflow YAML parse errors
- Missing input files
- Agent registration in `config.yaml`

For checking prompt **content** changes you do need a real call. Limit
the scope:

```bash
# Future: limit to a single agent (not yet implemented)
lovarch run my-test-project --only-agent concept-designer
```

Until that lands, use a minimal `my-test-project` with the smallest
brief possible and run a real Premium invocation. The CLI prints
estimated cost before kickoff.

## Common pitfalls

### "I edited and don't see the change"

- `lovarch dev show-squad-root` to confirm which path the CLI is reading.
- If Source is `bundled`, your env var isn't set — `echo $LOVARCH_SQUAD_SRC`
- If Source is `override ($LOVARCH_SQUAD_SRC)`, you edited the right
  file but maybe the wrong section — re-check the diff in your editor.

### "Refresh shows files I didn't change"

`lovarch dev refresh-squad` wipes the target and re-copies from source.
Pre-existing staged changes that hadn't been promoted from DEV are
preserved (they live in DEV). If you see unexpected diffs after a
refresh, it usually means someone else edited the monorepo since your
last refresh.

### "Brew users still see the old behavior"

`brew install lovarch-cli` installs the LATEST published release. After
a `git tag v0.X.Y && git push`, the auto-bump opens a PR on the tap;
once merged, users get the update on `brew upgrade lovarch-cli`. Until
then, only DEV (`LOVARCH_SQUAD_SRC`) and STAGED (your local
`lovarch_cli/squad/`) see the new code.

### "I want to edit STAGED for a one-off experiment"

Don't. Use `LOVARCH_SQUAD_SRC=/path/to/experimental/copy lovarch run ...`
instead. STAGED edits are wiped on the next refresh.

## Related docs

- [squad-vendoring.md](./squad-vendoring.md) — why the vendor split exists,
  what's vendored vs not
- [release-process.md](./release-process.md) — semver, tag conventions,
  automation flow
- [v0.1.0-handoff.md](./v0.1.0-handoff.md) — first-release setup notes
  (mostly historical now)
- [CONTRIBUTING.md](../CONTRIBUTING.md) — code style, commit
  conventions, PR template
