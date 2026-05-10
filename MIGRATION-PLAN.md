# lovarch-cli — Migration Runbook (EXECUTED 2026-05-10)

> **Status: ✅ SPLIT COMPLETED.** Este documento é histórico do split do CLI do monorepo Lovarch para repo standalone, executado durante a sessão Orion 2026-05-10.

## What was done

### 1. Repo created
- URL: https://github.com/ArchPrime-official/lovarch-cli
- Visibility: **public**
- License: MIT
- Created: 2026-05-10
- Org: ArchPrime-official (Pablo é admin)

### 2. History preserved via `git filter-repo`
Source: `feat/lovarch-cli-run-command` branch do monorepo Lovarch (rebased contra main, contém tudo até Fase A.6).

Comando executado:
```bash
git clone --no-local /Users/pablo/Lovarch /tmp/lovarch-cli-split/source
cd /tmp/lovarch-cli-split/source
git checkout feat/lovarch-cli-run-command
git filter-repo --subdirectory-filter cli/ --force
git remote add origin https://github.com/ArchPrime-official/lovarch-cli.git
git branch -M main
git push -u origin main --force
```

Resultado: 13 commits do CLI preservados (foundation → Fase A.6), paths reescritos removendo prefix `cli/`. 8080 commits totais escaneados, 1.11s tempo total.

### 3. Working dir local
Clone em `/Users/pablo/lovarch-cli/`:
```bash
git clone https://github.com/ArchPrime-official/lovarch-cli.git /Users/pablo/lovarch-cli
cd /Users/pablo/lovarch-cli
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/   # → 137 passed in 0.92s ✓
lovarch info    # ✓ funciona
```

### 4. CI workflow
Adicionado `.github/workflows/ci.yml`:
- pytest matrix Python 3.11 / 3.12 / 3.13
- pyflakes em `lovarch_cli/` + `tests/`
- smoke test `lovarch --version` + `lovarch info` + `arch --version` (alias)

### 5. To-do: delete from monorepo
PR separado abre no monorepo Lovarch removendo `cli/` (após Pablo confirmar repo standalone está estável). Edge Functions `cli-*` em `supabase/functions/` permanecem no monorepo (server-side).

---

## Workflow daily após o split

### Editar o CLI
```bash
cd /Users/pablo/lovarch-cli
# squad invocado do monorepo Lovarch (claude code multi-dir) edita arquivos
git checkout -b feat/new-thing
git add . && git commit -m "feat: ..."
git push -u origin feat/new-thing
gh pr create --fill
```

### Adicionar Edge Function (server-side)
EFs `cli-*` ficam no monorepo Lovarch:
```bash
cd /Users/pablo/Lovarch
git checkout -b feat/cli-new-ef
# editar supabase/functions/cli-new-ef/index.ts
git push && gh pr create
# Vercel/Supabase pipeline deploya
```

### Squads
Squads continuam no monorepo Lovarch. Claude Code com multi-dir abre ambos:
- `/Users/pablo/Lovarch` — squads + EFs + plataforma
- `/Users/pablo/lovarch-cli` — CLI source

Squad invocado de qualquer dir consegue editar arquivos do outro via path absoluto.

---

## Architecture decision: 2 repos, sem submodule

Considered:
- **A**: Não split (manter `cli/` no monorepo) — perde repo público elegante
- **B**: Split + worktree paralelo (escolhido) — 2 repos, multi-dir Claude Code
- **C**: Split + submodule — overhead de bumpar SHA toda mudança CLI

**Decisão Pablo (2026-05-10):** B porque:
1. CLI vai mudar **muito** (5-10× por semana durante curso). Submodule = 2 PRs por mudança.
2. Pablo já tem fricção com submodule pattern dos squads (`squads/strategic-management` aparece dirty).
3. Acesso aos squads é idêntico em B e C (multi-dir Claude Code).

---

## Próximos passos (Fase B.2)

Pendente — autorização Pablo necessária:

1. **PyPI publish setup**
   - GitHub Actions workflow `.github/workflows/publish-pypi.yml`
   - Trigger: push de tag `v*`
   - Build: `python -m build` → wheel + sdist
   - Upload: `twine upload` com `PYPI_API_TOKEN` secret
   - Test: `pipx install lovarch-cli` em CI matrix

2. **Homebrew formula**
   - Tap: `homebrew-lovarch` (org-level) ou `homebrew-tap` (user-level)
   - Formula `Formula/lovarch-cli.rb` referenciando PyPI tarball
   - Test em macOS via `brew install --build-from-source`

3. **First release**
   - Bump `version.py` 0.1.0
   - Tag `v0.1.0` → triggers publish workflow
   - GitHub Release com changelog (gerado de `git log --oneline`)

4. **README polish + course link**
   - Adicionar getting started passo-a-passo
   - Link curso https://lovarch.com/corso
   - Add screenshots `lovarch info` / `lovarch audit` (Rich panels)

Estimate: 1-2 dias trabalho com plano em mãos.

---

## Pegadinhas resolvidas no split

1. **PR #961 ainda OPEN durante split**: branch local `feat/lovarch-cli-run-command` rebased contra main resolveu cherry-pick conflict (audit já em main via PR #960). Filter-repo executado a partir do branch local que tem tudo. Quando PR #961 mergear no monorepo (paralelo), o lovarch-cli repo já está consistente.

2. **Org existe + permissions**: `gh api orgs/ArchPrime-official` confirmou Pablo tem `members_can_create_repositories: true`. Token gh tem scopes `repo + read:org` suficientes pra criar repo público.

3. **`git filter-repo` performance**: 8080 commits processados em 1.11s. Repacking + cleaning total 1.81s. Trivial pra repo desse tamanho.

4. **Test parity**: `pytest tests/` → 137 passed em ambos os repos (monorepo `cli/` e standalone `lovarch-cli`). Zero diferença de comportamento.

5. **`arch` alias preservado**: pyproject.toml mantém `arch = "lovarch_cli.cli:app"` como entry point secundário (backward-compat pra muscle memory).

---

## Reverting (caso precise)

Se algo der muito errado:
1. `cli/` ainda existe no monorepo Lovarch (PR de delete será separado e reversível via revert)
2. Histórico Git do monorepo preserva tudo
3. Repo `lovarch-cli` pode ser deletado via `gh repo delete ArchPrime-official/lovarch-cli --yes`

Mas todos os tests passam em ambos os lados — não há razão pra reverter.
