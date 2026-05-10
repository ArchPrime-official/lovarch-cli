# Squad vendoring strategy

> Status: Active since 2026-05-10 (Fase B.1.5 of CLI split)

## Why we vendor the squad

`lovarch-cli` orchestrates a real squad of agents/tasks/workflows that lives
in the **monorepo** Lovarch (`/Users/pablo/Lovarch/squads/architettura-progetto/`).
The standalone repo `ArchPrime-official/lovarch-cli` does not have direct access
to that source — so the squad payload must be **vendored** (committed) inside
this repo at `lovarch_cli/squad/`.

Without a populated `lovarch_cli/squad/`:

- `arch run <workflow>` cannot start (no `pipeline_runner.py`)
- `arch init <name> --sample` cannot copy the starter project
- `arch info` still works (it's a static panel) but is misleading

## What is vendored

| Path inside `lovarch_cli/squad/` | Source | Approx size |
|---|---|---|
| `agents/` | `squads/architettura-progetto/agents/` | ~290KB |
| `tasks/` | `squads/architettura-progetto/tasks/` | ~32KB |
| `workflows/` | `squads/architettura-progetto/workflows/` | ~8KB |
| `checklists/` | `squads/architettura-progetto/checklists/` | ~36KB |
| `templates/` | `squads/architettura-progetto/templates/` | ~40KB |
| `scripts/` | `squads/architettura-progetto/scripts/` | ~340KB |
| `data/mocks/` | `squads/architettura-progetto/data/mocks/` | ~8KB |
| `config.yaml` + `README.md` | top-level squad files | ~26KB |
| **Total** | | **~830KB** |

## What is NOT vendored

`data/sample-input/` and `data/sample-input-villa-chianti/` (~49MB combined —
mostly JPG photos + DXF/PDF/IFC files for the demo project). They are excluded
because:

1. A 50MB `pip install lovarch-cli` is unfriendly for a CLI BETA
2. The sample is read-only and only consumed by `arch init --sample`
3. Updating the sample shouldn't require a CLI release

These files ship via **GitHub Releases** asset:
[`sample-villa-chianti.zip`](https://github.com/ArchPrime-official/lovarch-cli/releases/latest).

When `arch init --sample` cannot find the sample inside `lovarch_cli/squad/`,
it prints a clear message instructing the user to download and unzip the
release asset. (Future: lazy auto-download with cache in `~/.lovarch/cache/`.)

## How to refresh the vendor (Pablo only)

When you change something in `/Users/pablo/Lovarch/squads/architettura-progetto/`
and want to propagate to the standalone repo:

```bash
cd /Users/pablo/lovarch-cli
git checkout -b chore/sync-squad-vendor
python3 scripts/refresh_squad_vendor.py
git diff --stat lovarch_cli/squad/
# Review the diff carefully — it should match the change you made in the monorepo.
git add lovarch_cli/squad/
git commit -m "chore(vendor): refresh squad payload from monorepo"
git push -u origin chore/sync-squad-vendor
gh pr create --fill
```

The script reads from `/Users/pablo/Lovarch/squads/architettura-progetto/`,
wipes `lovarch_cli/squad/`, and copies everything except the heavy
sample-inputs. Same logic as the build hook (`scripts/sync_squad.py`).

## Build hook behavior (`scripts/sync_squad.py`)

The hatchling build hook runs at `pip install -e .` / `python -m build`:

- **Standalone repo** (no sibling squads/): **NO-OP** — preserves the
  committed vendor in `lovarch_cli/squad/`. ✅
- **Monorepo dev** (sibling squads/architettura-progetto/ exists): wipes
  `lovarch_cli/squad/` and re-syncs from the sibling. Used during local dev
  in `/Users/pablo/Lovarch/cli/` (note: monorepo `cli/` will be deleted
  soon — see Fase B.1 cleanup PR).

In both modes, sample-inputs are skipped via `EXCLUDE_RELATIVE` in both
scripts.

## Future work (Fase B.1.6)

Implement lazy auto-download for `arch init --sample`:

- Detect missing `lovarch_cli/squad/data/sample-input-villa-chianti/`
- Check `~/.lovarch/cache/sample-villa-chianti/` first
- If not cached, fetch the release asset over HTTPS with progress bar
- Verify SHA256 against a checksum we ship in the wheel
- Extract to cache, then copy from cache to project input/

Ticket: TBD — not blocking BETA (current message is clear and actionable).
