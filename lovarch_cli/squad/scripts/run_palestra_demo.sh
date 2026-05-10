#!/usr/bin/env bash
# ================================================================================
# Run Palestra Demo · Squad Architettura-Progetto
#
# Orchestratore principale per la demo Salone del Mobile 2026.
# Modalità:
#   --simulate         Usa simulator (sicuro, fake-realistic, ~14 min)
#   --simulate --fast  Simulator velocizzato 5× (~3 min, per test)
#   --real             Esegue squad reale via Claude Code (futuro)
#   --check            Solo check prerequisites, no run
#
# Default: --simulate (più sicuro per la palestra)
#
# Usage:
#   ./run_palestra_demo.sh                  # default safe demo (simulate)
#   ./run_palestra_demo.sh --simulate --fast  # quick test
#   ./run_palestra_demo.sh --check          # health check only
# ================================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQUAD_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOVARCH_DIR="$(cd "${SQUAD_DIR}/../.." && pwd)"
SECRETS_FILE="${HOME}/.lovarch/secrets.env"

PROJECT_INPUT_DIR="${HOME}/projects/attico-brera"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GOLD='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
log()   { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}⚠${NC} $*"; }
err()   { echo -e "${RED}✗${NC} $*" >&2; }

banner() {
  echo ""
  echo -e "${GOLD}════════════════════════════════════════════════════════════════════${NC}"
  echo -e "${GOLD}  $1${NC}"
  echo -e "${GOLD}════════════════════════════════════════════════════════════════════${NC}"
  echo ""
}

# ------------------------------------------------------------------------------
# Args
# ------------------------------------------------------------------------------
MODE="simulate"
SPEED="1.0"
CHECK_ONLY=0
USER_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --simulate) MODE="simulate"; shift ;;
    --real)     MODE="real"; shift ;;
    --check)    CHECK_ONLY=1; shift ;;
    --fast)     SPEED="5.0"; shift ;;
    --speed)    SPEED="$2"; shift 2 ;;
    --user-id)  USER_ID="$2"; shift 2 ;;
    --help|-h)
      head -22 "$0" | tail -19
      exit 0 ;;
    *)
      err "Unknown arg: $1"
      exit 1 ;;
  esac
done

# ------------------------------------------------------------------------------
# Banner
# ------------------------------------------------------------------------------
banner "Squad Architettura-Progetto · Palestra Demo Runner"
log "Mode:           $MODE"
log "Speed:          ${SPEED}× $([ "$SPEED" = "1.0" ] && echo '(real time)' || echo '(accelerated)')"
log "Squad dir:      $SQUAD_DIR"
log "Lovarch dir:    $LOVARCH_DIR"
log "Project input:  $PROJECT_INPUT_DIR"
echo ""

# ------------------------------------------------------------------------------
# Step 1 · Check prerequisites
# ------------------------------------------------------------------------------
banner "Step 1 · Pre-flight checks"

PASS=1
fail() { err "$1"; PASS=0; }

# Python 3
if command -v python3 >/dev/null 2>&1; then
  ok "python3: $(python3 --version)"
else
  fail "python3 missing · brew install python@3.11"
fi

# ezdxf
if python3 -c "import ezdxf" 2>/dev/null; then
  ok "ezdxf: $(python3 -c 'import ezdxf; print(ezdxf.__version__)')"
else
  warn "ezdxf missing · pip3 install --user ezdxf"
fi

# Secrets file
if [[ -f "$SECRETS_FILE" ]]; then
  ok "secrets file: $SECRETS_FILE"
  source "$SECRETS_FILE" 2>/dev/null || true
else
  fail "secrets file missing: $SECRETS_FILE"
fi

# Mapbox token
if [[ -n "${MAPBOX_TOKEN:-}" ]]; then
  ok "MAPBOX_TOKEN: configured (${MAPBOX_TOKEN:0:20}...)"
else
  fail "MAPBOX_TOKEN missing in $SECRETS_FILE"
fi

# Supabase secrets (only required for real run, optional for dry-run)
if [[ -n "${SUPABASE_URL:-}" && -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]; then
  ok "Supabase: $SUPABASE_URL"
elif [[ "$MODE" = "simulate" && $CHECK_ONLY -eq 0 ]]; then
  warn "Supabase secrets missing — simulator richiede SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY"
  warn "Aggiungi in $SECRETS_FILE per inserire dati nel DB"
fi

# Sample input files
if [[ -f "$SQUAD_DIR/data/sample-input/briefing-cliente.md" ]]; then
  ok "briefing-cliente.md: $(wc -l < "$SQUAD_DIR/data/sample-input/briefing-cliente.md") righe"
else
  fail "briefing-cliente.md missing"
fi

# Templates
TEMPLATES_FOUND=$(find "$SQUAD_DIR/templates" -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
if [[ "$TEMPLATES_FOUND" -ge 4 ]]; then
  ok "templates: $TEMPLATES_FOUND files"
else
  fail "templates incomplete (found $TEMPLATES_FOUND, expected ≥4)"
fi

# Prezzario
if [[ -f "$SQUAD_DIR/data/prezzario-lombardia-sample.json" ]]; then
  PREZZI_COUNT=$(python3 -c "import json; print(len(json.load(open('$SQUAD_DIR/data/prezzario-lombardia-sample.json'))['voci']))" 2>/dev/null || echo "?")
  ok "prezzario lombardia: $PREZZI_COUNT voci"
else
  fail "prezzario sample missing"
fi

# Final check verdict
if [[ $PASS -eq 0 ]]; then
  err ""
  err "Pre-flight FAILED. Fix issues sopra e riprova."
  exit 1
fi

ok ""
ok "All checks passed."

# Stop here if --check only
if [[ $CHECK_ONLY -eq 1 ]]; then
  banner "Check-only mode · stopping"
  exit 0
fi

# ------------------------------------------------------------------------------
# Step 2 · Prepare project input directory
# ------------------------------------------------------------------------------
banner "Step 2 · Preparing project input"

mkdir -p "$PROJECT_INPUT_DIR/01-input/foto"
log "Created $PROJECT_INPUT_DIR/"

# Copy briefing
cp "$SQUAD_DIR/data/sample-input/briefing-cliente.md" "$PROJECT_INPUT_DIR/01-input/briefing-cliente.md"
ok "briefing-cliente.md copied"

# Generate DWG
if [[ ! -f "$PROJECT_INPUT_DIR/01-input/stato-attuale.dxf" ]]; then
  log "Generating stato-attuale.dxf..."
  if python3 "$SQUAD_DIR/scripts/generate_attico_brera_dwg.py" \
      "$PROJECT_INPUT_DIR/01-input/stato-attuale.dxf" >/dev/null 2>&1; then
    ok "stato-attuale.dxf generated ($(du -h "$PROJECT_INPUT_DIR/01-input/stato-attuale.dxf" | cut -f1))"
  else
    warn "DWG generation failed (ezdxf not installed?)"
  fi
else
  ok "stato-attuale.dxf already exists"
fi

# Sync templates
mkdir -p "$PROJECT_INPUT_DIR/templates"
cp -n "$SQUAD_DIR/templates"/*.md "$PROJECT_INPUT_DIR/templates/" 2>/dev/null || true
ok "templates synced ($(ls "$PROJECT_INPUT_DIR/templates" | wc -l | tr -d ' ') files)"

# Sync prezzario
mkdir -p "$PROJECT_INPUT_DIR/data"
cp -n "$SQUAD_DIR/data/prezzario-lombardia-sample.json" "$PROJECT_INPUT_DIR/data/" 2>/dev/null || true
ok "prezzario synced"

log ""
log "Project input ready: $PROJECT_INPUT_DIR"
ls -la "$PROJECT_INPUT_DIR/01-input"

# ------------------------------------------------------------------------------
# Step 3 · Resolve user_id (admin Pablo)
# ------------------------------------------------------------------------------
banner "Step 3 · Resolving Supabase user_id"

if [[ -z "$USER_ID" && -n "${SUPABASE_URL:-}" && -n "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]; then
  USER_ID=$(curl -s "${SUPABASE_URL}/rest/v1/profiles?email=eq.pablo@archprime.io&select=id" \
    -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d[0]['id'] if d else '')" 2>/dev/null || echo "")
fi

if [[ -n "$USER_ID" ]]; then
  ok "user_id: $USER_ID"
else
  warn "user_id not resolved · usando placeholder UUID"
  USER_ID="00000000-0000-0000-0000-000000000000"
fi

# ------------------------------------------------------------------------------
# Step 4 · Execute simulation OR real squad
# ------------------------------------------------------------------------------
banner "Step 4 · Execution"

if [[ "$MODE" = "simulate" ]]; then
  log "Running simulator at speed ${SPEED}×..."
  log ""
  python3 "$SQUAD_DIR/scripts/simulate_squad_execution.py" \
    --user-id "$USER_ID" \
    --speed "$SPEED"
elif [[ "$MODE" = "real" ]]; then
  warn "REAL mode: launching Claude Code with squad architettura-progetto"
  warn "Questa modalità richiede Claude Code installato e configurato."
  echo ""
  log "Comando suggerito:"
  echo ""
  echo -e "${GOLD}    cd $LOVARCH_DIR${NC}"
  echo -e "${GOLD}    claude \"Squad architettura-progetto: esegui workflow dal-brief-al-cantiere${NC}"
  echo -e "${GOLD}    con input $PROJECT_INPUT_DIR/01-input/\"${NC}"
  echo ""
  read -r -p "Lancio? (y/N) " yn
  if [[ "$yn" = "y" || "$yn" = "Y" ]]; then
    cd "$LOVARCH_DIR"
    claude "Squad architettura-progetto: esegui workflow dal-brief-al-cantiere con input $PROJECT_INPUT_DIR/01-input/"
  else
    log "Skipped."
    exit 0
  fi
fi

# ------------------------------------------------------------------------------
# Step 5 · Final
# ------------------------------------------------------------------------------
banner "Demo complete"

ok "Esecuzione completata."
log ""
log "Per visualizzare la live page e il dossier:"
log "  https://lovarch.com/admin · login admin"
log "  Vai su: /admin/squad-execution/{execution_id}/live"
log "  Poi:    /admin/squad-execution/{execution_id}/dossier"
log ""
log "L'ID dell'esecuzione è stampato sopra. Buona presentazione!"
