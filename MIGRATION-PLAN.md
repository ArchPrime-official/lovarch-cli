# archprime-cli — Repo Migration Plan

> **Decisão (2026-05-10, Pablo + Orion):** mantemos `cli/` no monorepo Lovarch durante a alpha (v0.x). Splitamos pra repo público dedicado **antes do v1.0** (gate de publicação PyPI).
>
> Esta decisão equilibra três coisas: (1) momentum pro lançamento do **curso IA Avanzato €1.497**, que precisa do CLI funcional rápido; (2) integridade arquitetural (squad sibling, EFs no Lovarch CI, GDPR/disclaimer IT sync); (3) compromisso público com PyPI quando estável.

## Por que NÃO splitar ainda

| Razão | Detalhe |
|-------|---------|
| **Fricção dev** | `scripts/sync_squad.py` lê `../squads/architettura-progetto/` (sibling). Splitar agora = configurar git submodule + atualizar build hook. Custo 1-2h sem ganho imediato. |
| **EFs vivem no Lovarch** | `cli-signup`, `cli-account-delete` ficam em `supabase/functions/`. Cada EF nova = PR no Lovarch, sempre. Mesmo após split, dev de feature toca 2 repos — frição cross-repo. |
| **Compliance sync** | Disclaimer IT (CILA/SCIA), texto GDPR, disclaimer regulatório vem de `squads/architettura-progetto/data/`. Mesmo repo = atualização atômica. |
| **PRs já abertos** | #937 (foundation) + #938 (Epic 2) já em revisão. Splitar agora = recriar history em outro repo, perder squash credit, refazer review. |

## Por que SPLITAR pré-v1.0

| Razão | Detalhe |
|-------|---------|
| **PyPI publish exige source público** | Repository link em `pyproject.toml` aponta pro source. Lovarch é privado → link 404. Aluno do curso clica e dá erro. |
| **License coherence** | Lovarch é proprietário (sem LICENSE root). archprime-cli é MIT. Coexistir num mesmo repo confunde — pessoas podem assumir todo Lovarch é MIT. |
| **Issues + community** | Aluno do curso reporta bug onde? Repo público dedicado é a doca natural. Tickets do CLI misturados com tickets web Lovarch é ruído. |
| **Versioning independente** | Tags `archprime-cli-v0.1.0` desacopladas de `lovarch-v...`. Semver claro. |
| **Auditability** | Comunidade B2B Italia pode auditar source antes de instalar. Privado = dúvida. |

## Quando splitar

**Trigger explícito (qualquer um):**
- v1.0.0-rc.1 prestes a publicar PyPI
- ≥10 alunos do curso pediram source público
- Compliance team Italia exige audit do CLI
- Squad architettura-progetto vira git submodule no Lovarch (mais provável Q3/2026)

**Não-triggers (não splitar por estes):**
- "Foundation parece estável"
- "Quero open-source antes de marketing"
- "Outro projeto similar splitou"

## Como splitar (runbook)

Quando o trigger acontecer:

### 1. Criar repo destino

```bash
# Recomendado: ArchPrime-official org (mesma org dos squads)
gh repo create ArchPrime-official/archprime-cli \
  --public \
  --description "AI-powered architectural project execution CLI by Lovarch" \
  --license MIT
```

### 2. Extrair history preservando autoria

```bash
# Trabalhar num clone separado, NÃO no working tree principal
git clone https://github.com/ByPabloRuanL/lovarch.git /tmp/lovarch-cli-extract
cd /tmp/lovarch-cli-extract

# Instalar git-filter-repo (preferred over git filter-branch)
brew install git-filter-repo  # ou: pip install git-filter-repo

# Extrair APENAS histórico de cli/
git filter-repo --path cli/ --path-rename cli/:

# Adicionar remote do novo repo
git remote add origin https://github.com/ArchPrime-official/archprime-cli.git
git push -u origin main
```

### 3. Configurar build hook pra squad como submodule

Adicionar `.gitmodules` no novo repo:

```ini
[submodule "squads/architettura-progetto"]
    path = squads/architettura-progetto
    url = https://github.com/ArchPrime-official/PrimeSquads-architettura-progetto.git
```

(Squad provavelmente vira submodule do Lovarch primeiro — checar status com `bump-all-squads.sh`)

Atualizar `scripts/sync_squad.py`:

```python
# Antes (monorepo): repo_root = cli_root.parent
# Depois (split):  squad_src = cli_root / "squads" / SQUAD_NAME  (submodule)
```

### 4. Remover do Lovarch monorepo

```bash
cd /Users/pablo/Lovarch
git checkout -b chore/remove-cli-after-split
git rm -r cli/
# Substituir por submodule pointer (opcional — só se Lovarch precisar buildar CLI no CI):
git submodule add https://github.com/ArchPrime-official/archprime-cli.git cli
git commit -m "chore: split archprime-cli into ArchPrime-official/archprime-cli"
gh pr create
```

### 5. Atualizar `pyproject.toml` Repository links

```toml
Repository = "https://github.com/ArchPrime-official/archprime-cli"
Issues = "https://github.com/ArchPrime-official/archprime-cli/issues"
Documentation = "https://docs.archprime.io/cli"
```

### 6. Setup CI/CD pro PyPI publish no novo repo

`.github/workflows/publish.yml`:
- Trigger em tag `v*.*.*`
- `uv build` → twine upload
- Secret `PYPI_TOKEN` (gerar token PyPI escopo project)

### 7. Cross-link nos docs

- Lovarch CLAUDE.md: nota que CLI mudou de repo
- ArchPrime-official/archprime-cli README: linka pra Lovarch como backend premium
- docs.archprime.io: explica arquitetura free/premium e onde contribuir

## Riscos da migração

| Risco | Mitigação |
|-------|-----------|
| Perder commits/autoria | `git filter-repo` preserva. Validar com `git log --oneline\|wc -l` antes/depois. |
| Squad sync quebrar | Testar `pip install -e .` no novo repo antes de remover do Lovarch. |
| PyPI name conflict | Reservar `archprime-cli` no PyPI **agora** (TestPyPI sandbox + reserve real PyPI). |
| Imports quebrarem em Lovarch | CLI Python NÃO é importado por Lovarch web. Verificar com `grep -r "archprime_cli" src/ supabase/`. |

## Histórico de decisões

| Data | Quem | Decisão |
|------|------|---------|
| 2026-05-10 | Pablo + Orion | Mantém monorepo agora, split planejado pré-v1.0. PyPI público confirmado como canal de distribuição final. |
