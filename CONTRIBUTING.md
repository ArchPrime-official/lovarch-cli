# Contributing to `lovarch-cli`

Thanks for your interest in improving the CLI. This project is currently in
**BETA** (v0.1.x) and is the delivery vehicle for the
[Corso IA Avanzato per Architetti](https://lovarch.com/corso). Contributions
are welcome — please read this short guide first.

## Development setup

```bash
git clone https://github.com/ArchPrime-official/lovarch-cli.git
cd lovarch-cli
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Verify
lovarch --version
pytest tests/         # → 142 passing in ~1s
```

Python 3.11+ is required. CI tests against 3.11, 3.12, 3.13.

## Local quality gates

Before opening a PR, ensure these pass:

```bash
# pyflakes (skips vendored squad code)
find lovarch_cli tests -type d -name squad -prune -o -name '*.py' -print | xargs pyflakes

# Full test suite
pytest tests/ -q

# Smoke (real binary works)
lovarch --version
lovarch info
```

CI runs the same checks plus a smoke job that asserts `arch` (the
backward-compat alias) also works.

## Commit conventions

We use [Conventional Commits](https://www.conventionalcommits.org/) for the
prefix:

- `feat:` — new user-visible capability
- `fix:` — bug fix
- `refactor:` — internal change without behavior shift
- `docs:` — documentation only
- `test:` — test additions / fixes
- `chore:` — build, deps, tooling
- `perf:` — performance improvement

Format the subject line in imperative mood, ≤72 chars. Body explains the
*why*, not the *what* (the diff already shows the what).

## Pull requests

1. Branch from `main`: `git checkout -b feat/your-thing`
2. Make focused commits — one logical change per commit.
3. Run the local quality gates above.
4. Open the PR against `main`. Use the PR template.
5. CI must pass (`pytest + pyflakes (3.11)`, `(3.12)`, `(3.13)`, `smoke`)
   before review.
6. The maintainer (Pablo) will squash-merge approved PRs.

Branch protection requires CI status checks. Force-pushes and branch
deletions on `main` are disabled.

## What goes WHERE

| Layer | Lives in |
|---|---|
| CLI commands (`lovarch <subcommand>`) | `lovarch_cli/commands/<name>.py` |
| Auth / token storage / PKCE | `lovarch_cli/auth/` |
| Backend HTTP clients | `lovarch_cli/clients/` |
| Credits resolution | `lovarch_cli/credits/` |
| i18n strings | `lovarch_cli/i18n/translations/{it,pt,en,es}.json` |
| Sample download / cache | `lovarch_cli/sample_downloader.py` |
| Build hook (squad sync) | `scripts/sync_squad.py` |
| Manual vendor refresh | `scripts/refresh_squad_vendor.py` |
| **Vendored squad source** | `lovarch_cli/squad/` (do NOT edit — read [docs/squad-vendoring.md](./docs/squad-vendoring.md)) |
| Tests | `tests/test_*.py` |
| GitHub Actions workflows | `.github/workflows/` |

## Adding a new command

1. Create `lovarch_cli/commands/<name>.py` with a Typer callback.
2. Register it in `lovarch_cli/cli.py` (lazy import in the typer app setup).
3. Add `<name>.<key>` translations in all four languages
   (`lovarch_cli/i18n/translations/{it,pt,en,es}.json`) — Italian first.
4. Write tests in `tests/test_<name>.py` using `typer.testing.CliRunner`.
5. Document the command in the README "Comandi disponibili" table.
6. Add a CHANGELOG entry under `[Unreleased]`.

## i18n discipline

Italian (`it.json`) is the reference language. When adding a key:

1. Add to `it.json` first with the production copy.
2. Translate into `pt`, `en`, `es` keeping the **same key structure**.
3. The parity test (`tests/test_i18n_loader.py::test_all_bundled_langs_have_same_keys`)
   will fail CI if any key is missing in any language.

Use `t('namespace.key', lang=current_lang(), placeholder=value)` from
`lovarch_cli.i18n` — never inline strings.

## Squad changes

The squad (`lovarch_cli/squad/`) is vendored from the source-of-truth repo
in the Lovarch monorepo (`/Users/pablo/Lovarch/squads/architettura-progetto/`).

**Do NOT edit `lovarch_cli/squad/` directly in this repo.** Changes there
will be wiped the next time the vendor is refreshed. Instead:

1. Edit upstream in the Lovarch monorepo
2. Run `python3 scripts/refresh_squad_vendor.py` here
3. Commit the diff in `lovarch_cli/squad/`

See [docs/squad-vendoring.md](./docs/squad-vendoring.md) for the full story.

## Release process

Maintainer-only — see [docs/release-process.md](./docs/release-process.md)
for tagging conventions, PyPI/Homebrew automation, and rollback procedures.

## Reporting issues

- 🐛 Bug? Use the [bug report template](https://github.com/ArchPrime-official/lovarch-cli/issues/new?template=bug-report.yml)
- 💡 Feature idea? Use the [feature request template](https://github.com/ArchPrime-official/lovarch-cli/issues/new?template=feature-request.yml)
- 🔐 Security issue? Email pablo@archprime.io — do NOT open a public issue.

## License

By contributing you agree that your contributions are licensed under the
[MIT License](./LICENSE) of this project.
