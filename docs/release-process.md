# Release process

> Status: Active since 2026-05-10 (updated 2026-05-11 to reflect PyPI-deferred
> distribution strategy). Required reading before cutting any release.

## TL;DR — cut a release

```bash
cd /Users/pablo/lovarch-cli
git checkout main && git pull
# 1. Bump version
$EDITOR lovarch_cli/version.py    # e.g. "0.1.0" → "0.1.1"
git commit -am "chore: bump v0.1.1"
# 2. Tag + push (semver) — triggers automation
git tag v0.1.1
git push origin main v0.1.1
```

What happens next is automated by GitHub Actions:

1. **`.github/workflows/attach-to-release.yml`** runs on any `v*` tag:
   - Builds wheel + sdist with `python -m build`
   - Creates or updates the GitHub Release for the tag
   - Attaches `lovarch_cli-X.Y.Z-py3-none-any.whl` and `lovarch_cli-X.Y.Z.tar.gz`
   - Marks the release as pre-release if the tag has a `-beta.X` / `-rc.X`
     suffix

2. **`.github/workflows/bump-homebrew-formula.yml`** runs on final tags only
   (skips pre-release suffixes):
   - Computes the source-tarball SHA256
   - Opens a PR on `ArchPrime-official/homebrew-lovarch` updating
     `Formula/lovarch-cli.rb` with the new `url` + `sha256`
   - Requires `HOMEBREW_TAP_TOKEN` secret (fine-grained PAT scoped to the
     tap repo). If missing, the job exits with a `::notice::` log entry.

3. **`.github/workflows/publish-pypi.yml`** is **DORMANT** — set to
   `workflow_dispatch` only (manual trigger). Activate it later by either:
   - Manually: `gh workflow run publish-pypi.yml --ref v0.1.0 -f tag=v0.1.0`
   - Permanently: edit the workflow's `on:` to `push: tags: ['v*']`

## Distribution channels

| Channel | Status | Install command |
|---|---|---|
| Homebrew tap | ✅ Active | `brew tap archprime-official/lovarch && brew install lovarch-cli` |
| pipx from git | ✅ Active | `pipx install git+https://github.com/ArchPrime-official/lovarch-cli.git@v0.1.0` |
| GitHub Release wheel | ✅ Active | `pip install https://github.com/.../releases/download/v0.1.0/lovarch_cli-0.1.0-py3-none-any.whl` |
| PyPI | 💤 Deferred | `pip install lovarch-cli` — N/A until activated |

## Tag conventions

| Tag pattern | GitHub Release | Pre-release flag | Homebrew bump | PyPI |
|---|---|---|---|---|
| `v0.1.0` | ✅ Yes | No | ✅ Yes (PR) | 💤 Manual only |
| `v0.1.0-beta.1` | ✅ Yes | Yes | ❌ No | 💤 Manual only |
| `v0.1.0-rc.2` | ✅ Yes | Yes | ❌ No | 💤 Manual only |
| Anything not matching `v*` | (no match) | — | — | — |

## First-time setup (one-off, done by Pablo)

### Option A — Trusted Publishing (recommended)

No tokens to manage. Configure once at https://pypi.org/manage/account/publishing/:

- Owner: `ArchPrime-official`
- Repository: `lovarch-cli`
- Workflow: `publish-pypi.yml`
- Environment: `pypi`

Then in `publish-pypi.yml` swap the `twine upload` step for the
`pypa/gh-action-pypi-publish@release/v1` action. Skip the token step entirely.

### Option B — API token

```bash
# 1. Create the token at https://pypi.org/manage/account/token/
#    (scope: "Project: lovarch-cli" once the project exists, else "Entire account"
#    for the first manual upload)
# 2. Register as a repo secret
gh secret set PYPI_API_TOKEN --repo ArchPrime-official/lovarch-cli
# (paste the pypi-... token when prompted)
```

For Option B's first release, you may need to upload manually once so the
project name `lovarch-cli` is registered on PyPI (allowing project-scoped
tokens afterward):

```bash
cd /Users/pablo/lovarch-cli
python -m pip install --upgrade build twine
python -m build
twine upload dist/*   # uses ~/.pypirc or env vars
```

## Semver bump policy

- **MAJOR** (1.0.0 → 2.0.0): breaking CLI API — subcommand removed,
  flag renamed, project.yaml schema breaking change.
- **MINOR** (0.1.0 → 0.2.0): new subcommand, new agent in the squad,
  new language, new optional flag.
- **PATCH** (0.1.0 → 0.1.1): bug fix, dependency bump, copy fix,
  docs improvement, performance tweak.

Pre-1.0 we use `0.1.x` for both patches and minors — be conservative
about declaring 1.0 (it implies API stability promise).

## Pre-release flow

For BETA / RC testing without polluting PyPI:

```bash
# Tag with semver suffix
git tag v0.2.0-beta.1
git push origin main v0.2.0-beta.1
# → GitHub Release created (pre-release flag set)
# → wheel + sdist attached as assets
# → NO PyPI upload
```

Users install pre-releases from the GitHub Release directly:

```bash
pip install https://github.com/ArchPrime-official/lovarch-cli/releases/download/v0.2.0-beta.1/lovarch_cli-0.2.0b1-py3-none-any.whl
```

## Sample-input asset (separate from wheel)

`sample-villa-chianti.zip` (~21MB) is NOT bundled in the wheel — it lives as a
GitHub Release asset. When you ship a new release that changes the sample:

1. Cut the release tag (workflow auto-attaches wheel + sdist)
2. Manually re-zip + upload the sample-input over the GH UI, OR run:
   ```bash
   cd /Users/pablo/Lovarch/squads/architettura-progetto/data
   zip -r /tmp/sample-villa-chianti.zip sample-input-villa-chianti -x "*.DS_Store"
   gh release upload v0.2.0 /tmp/sample-villa-chianti.zip \
     --repo ArchPrime-official/lovarch-cli
   ```
3. Bump `SAMPLE_RELEASE_TAG` + `SAMPLE_ASSET_SHA256` in
   `lovarch_cli/sample_downloader.py`
4. Commit + cut a follow-up patch release with the new pin

See [`docs/squad-vendoring.md`](./squad-vendoring.md) for the bigger story.

## Rollback / yank

A bad release can be yanked from PyPI (still installable by pin, but not
selected by default):

```bash
twine upload --skip-existing  # if you just want to re-upload an idempotent fix
# To yank a specific release:
#   PyPI UI → project → manage release → Options → Yank
```

GitHub Release rollback:

```bash
gh release delete v0.X.Y --repo ArchPrime-official/lovarch-cli
git push --delete origin v0.X.Y    # remove the tag
```

## Checklist for the FIRST PyPI release (v0.1.0)

- [ ] CLI feature complete enough for `arch run` end-to-end in Free mode
- [ ] Course landing page references `pip install lovarch-cli`
- [ ] PyPI account / token configured (Option A or B above)
- [ ] Bump `lovarch_cli/version.py` to `"0.1.0"`
- [ ] Bump `SAMPLE_RELEASE_TAG` to `"v0.1.0"` in `sample_downloader.py`
       (only if you cut a fresh sample asset under the v0.1.0 release)
- [ ] Squash recent commits into a coherent CHANGELOG entry (if maintaining one)
- [ ] Tag + push → watch the workflow
- [ ] After PyPI lands: `pip install --upgrade lovarch-cli` from a fresh venv
       and verify `lovarch info` + `lovarch init test --sample` + `lovarch run`
