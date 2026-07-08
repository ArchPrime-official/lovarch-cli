# Handoff — 2026-07-08 · lead-flow do CLI free + páginas de login com marca

Sessão longa cobrindo 3 repos: **lovarch-cli**, **Lovarch** (web), **PrimeTeam** (CRM). Tudo mergeado e deployado.

## Releases do CLI (todas no brew via tap)

| Versão | O quê |
|---|---|
| 0.4.2 | Planta DXF profissional (release do commit já existente) |
| 0.4.3 | Auto-sync das skills em `~/.claude/skills` no start do CLI |
| 0.4.4 | Fix login redirect `lovarch.com` → `app.lovarch.com` (domínio centralizado em `config.DEFAULT_WEB_URL`) |
| 0.4.5 | Audit de todos os links (smoke real no browser): corrigidos 404 (`/cli-upgrade`,`/credits`,`/legal/cli-tos`,`/settings/account/delete`), removido `/corso` (não existe) |
| 0.4.6 | Onboarding free: `next_steps` apontava `init/audit/run` (removidos) → `skills install`/`cad genera`/`verifica misure` |
| 0.4.7 | Páginas de login (sucesso/erro do `local_server.py`) redesenhadas com marca Lovarch (símbolo SVG, oro, Outfit/DM Sans), **idioma único** vindo de `AuthServer(lang)` |

## Trabalho cross-repo (fluxo de lead free → CRM ArchPrime)

Decisão do Pablo: leads do CLI free vão pro **CRM PrimeTeam**, campanha nova **LOVARCH_CLI**; CTA de conversão = **Lovarch Premium (créditos)**.

- **PrimeTeam**: criada a campanha `LOVARCH_CLI` (via EF `campaigns-api`) + nova EF **`cli-lead-ingest`** (valida X-Lovarch-Secret, dedup por email OU telefone, atribui à campanha). PR #4983. ⚠️ Deploy manual necessário (ver débito 2).
- **Lovarch (web)**: EF **`cli-signup`** passou a espelhar o lead no PrimeTeam (best-effort) + fix `upgrade_url` e naming; tela **`/cli-auth`** naming `archprime-cli`→`lovarch-cli` (PR #1953, #1954).
- Ver memória [[cli-lead-flow-to-primeteam]] e [[lovarch-primeteam-bridge]].

## Deploys confirmados
- CLI 0.4.7 no brew (`lovarch --version` ✓).
- EF `cli-lead-ingest` viva (401 com secret errado); `cli-signup` deployada.
- Web PRs merged → Vercel.

## Smoke (o que vi)
- **E2E real**: `lovarch signup` (brew) → lead na campanha LOVARCH_CLI (count 0→1), **confirmado visualmente** em `primeteam.archprime.io/campagne` (Playwright autenticado). Lead de teste limpo dos 2 sistemas depois.
- **Páginas de login**: render real (fontes carregando) bateu com o preview aprovado.
- Docs Windows: `pipx install <wheel-url>` testado (sem git).

## Débitos abertos
1. **i18n órfãos** (`init`/`run`/`consolidate`.next_steps) nos 4 json do CLI — 0 referências, nunca exibidos. Dono: próximo que mexer em i18n. Fecha quando: remover das 4 línguas num release de higiene (paridade mantida).
2. **Deploy de EF nova no PrimeTeam é manual** — o `supabase-deploy` pula EF nova (detecção por grafo de imports). Sempre `supabase functions deploy <nome>` após merge. Registrado na memória [[primeteam-ef-deploy-gotcha]].

## Lições → memória
- [[cli-lead-flow-to-primeteam]], [[lovarch-primeteam-bridge]], [[primeteam-ef-deploy-gotcha]], [[playwright-primeteam-auth-via-session-json]].
