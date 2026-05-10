# Task: consolidate-dossier

> **Pattern:** AP-TP-001
> **Executor:** @progetto-chief (Tier 0 orchestrator)
> **Squad:** architettura-progetto

---

## task_name
Consolidate final dossier + Lovarch upload + git commit + CHANGELOG

## status
ACTIVE · stable · v1.0

## responsible_executor
- **agent**: @progetto-chief
- **executor_type**: AP-EP-002 (Agent + Python workers)
- **workers**: zipfile, git, supabase-py

## execution_type
**Final synchronous step** · Status: Validated → Done

## input
```yaml
required:
  all_tier1_outputs: "All Tier 1 deliverable files"
  qa_passes: "All applicable QA agents PASS"
  execution_id: "pm_squad_executions UUID"
  user_id: "Pablo admin UUID"
optional:
  git_tag_format: "squad-v{version}-{timestamp}"
```

## output
```yaml
files:
  - "~/projects/{slug}/README.md"
  - "~/projects/{slug}/manifest.json"  # SHA256 + sizes
  - "05-impresa/DOSSIER-IMPRESA.zip"  # if not already
lovarch:
  pm_documents_uploaded: number  # 27+ files
  pm_squad_executions_status: "completed"
  pm_squad_steps_count: number
git:
  commit_sha: string
  tag: string
final:
  live_tracking_url: string
  dossier_url: string
```

## action_items

### Phase A · Bootstrap project (BEFORE Tier 1 starts · @progetto-chief calls early)
1. `LovarchClient.create_project_complete()` · all-in-one
   - Creates `leads` row (Marco Rossini · CRM)
   - Creates `pm_projects` row (Attico Brera · linked to lead)
   - Creates `pm_phases` × 6 (Briefing/Definitivo/Pratiche/Esecutivo/DL/Consegna)
   - Creates `pm_budget_items` × 10 (default % breakdown · opere_edili 35%, impianti 15%, etc.)
   - Creates `financial_categories` "Onorari Architetto" (if not exists)
   - Creates `financial_transactions` × 5 (parent + 4 SAL installments 15/25/25/35%)
   - Creates `portal_clients` + `portal_project_access` + magic link
   - Creates `pm_squad_executions` row (status: running)
   - Returns: `{lead_id, project_id, phase_ids, budget_item_ids, finance_transaction_ids, portal, execution_id}`

1b. **AUTO-OPEN live tracking page in browser** (mandatory · Pablo must see progress real-time):
```python
import webbrowser
live_url = f"https://lovarch.com/admin/squad-execution/{execution_id}/live"
webbrowser.open(live_url, new=2)  # opens in new tab
```
This MUST happen IMMEDIATELY after pm_squad_executions row created. Squad does not wait for Tier 1 to start before opening browser.

### Phase B · Persist Tier 1 outputs progressively (during execution)
2. `@concept-designer` outputs → `LovarchClient.create_moodboard_analysis()` + `add_moodboard_assets()`
   - Insert `moodboard_analyses` (project_id linked)
   - Insert `moodboard_generated_assets` × 9 (asset_type: flatlay_complete | atmosphere | colors)
   - Note: NEW-HOME hero priority is flatlay_complete (3) > atmosphere (2) > colors (1)

3. `@concept-designer` 6 renders → `LovarchClient.save_render(project_id=..., metadata={ambient: ...})`
   - Each FLUX render → INSERT `render_assets` row (project_id MANDATORY)
   - Visible in `/new-home` ProjectDetailConnections tab + Project cover hero

4. `@cad-engineer` + `@bim-engineer` outputs → `LovarchClient.upload_documents_batch()`
   - Each DXF, IFC, PDF → upload Storage `pm-documents` bucket + INSERT `pm_documents` row
   - Linked to project_id + appropriate phase_id

5. `@capitolato-writer` outputs → `upload_documents_batch()` (capitolato + cronoprogramma + CAM xlsx)

6. `@computo-engineer` outputs → `upload_documents_batch()` (xlsx, pdf) + UPDATE `pm_budget_items` with actual values

7. `@pratiche-it` outputs → `upload_documents_batch()` (CILA, asseverazione, paesaggistica · phase_id = "Pratiche")

8. `@contratto-architect` outputs → `LovarchClient.create_contract(project_id=...)` + `upload_documents_batch()` (contract PDF)
   - INSERT `contracts` row (project_id linked) · visible in ProjectDetailContract tab

9. `@deliverable-builder` outputs → `upload_documents_batch()` (presentation HTML, etc.)

10. `LovarchClient.bulk_create_tasks(project_id, tasks=[...15 tasks])`
    - 15 team tasks with phase_id assignments + responsible + deadline

### Phase C · QA verification (Tier 2 after Tier 1 complete)
11. Verify all QA agents emitted PASS verdict (4/4 PASS required)
12. Run @quality-output `LovarchClient` integrity test:
    - Each `pm_documents.id` reachable + public_url returns HTTP 200
    - All `render_assets.project_id` set
    - `moodboard_analyses` has ≥1 generated_asset

### Phase D · Final consolidation
13. Generate README.md with project index + URLs
14. Compute SHA256 + size per file → manifest.json (uploaded as pm_documents row)
15. Build DOSSIER-IMPRESA.zip · upload to Storage · INSERT pm_documents row (doc_type: "dossier")
16. `LovarchClient.update_execution(status="completed", total_duration, total_steps)`
17. Append entry to data/CHANGELOG.md (local + uploaded as pm_documents)
18. Git stage + commit + tag (squad-v2.0.0-{timestamp})
19. Open Finder on project folder (macOS) + AUTO-OPEN browser tabs:
```python
import webbrowser, subprocess
webbrowser.open(f"https://lovarch.com/admin/squad-execution/{execution_id}/dossier", new=2)
webbrowser.open(f"https://lovarch.com/new-home", new=2)
subprocess.run(["open", f"~/projects/{slug}/"])  # macOS Finder
```
- `lovarch.com/admin/squad-execution/{id}/dossier` (clickable deliverables)
- `lovarch.com/new-home` (project visible in ProjectsPanel grid)
- `~/projects/{slug}/` (Finder with all 27 files)
- Magic link automatically sent to client email
20. Print summary console + return execution_id

## acceptance_criteria
- [ ] All QA agents PASS verdicts received
- [ ] README.md generated with all 8 subfolder links
- [ ] manifest.json with SHA256 of every deliverable
- [ ] All files uploaded to pm_documents (HTTP 200 verified)
- [ ] pm_squad_executions status = "completed"
- [ ] CHANGELOG.md updated
- [ ] Git commit + tag created
- [ ] Live URL + dossier URL printed

## dependencies
- **Libraries:**
  - zipfile (Python · DOSSIER.zip)
  - hashlib (SHA256)
  - git CLI
  - supabase-py
- **APIs:**
  - Supabase Storage (uploads)
  - Supabase REST (pm_documents inserts)
  - pm_squad_executions UPDATE
- **Files:**
  - All Tier 1 outputs aggregated
  - data/CHANGELOG.md (append)

## quality_gate
- **Gate:** QG-AP-1.5 (Output Completeness)
- **Reviewer:** @quality-output (already PASS prerequisite)
- **Final verification:** All 14 quality-output items PASS

## handoff
- **From:** @progetto-chief (self · final consolidation)
- **To:** Pablo (human · final delivery)
- **No further routing**

## veto_conditions
- Any QA agent NOT PASS → halt · re-route to retry
- Lovarch storage quota full → halt + notify Pablo
- Git commit fails → halt + investigate
- pm_documents insert error → halt · retry once

## estimated_time
**45-60 seconds**

## output_example
```
✓ All 4 QA agents PASS
✓ README.md generated · 8 subfolders linked
✓ manifest.json · 27 files · SHA256 verified
✓ DOSSIER-IMPRESA.zip · 15.2 MB
✓ Lovarch uploads: 27/27 (HTTP 200)
✓ pm_squad_executions: status=completed · duration=14m 32s · steps=20
✓ CHANGELOG.md updated · entry [Execution 1] appended
✓ Git commit: a3f8b2e · tag squad-v2.0.0-2026-04-25T14:46:32

Live tracking: https://lovarch.com/admin/squad-execution/5d585486-0991-4598-b880-171682ea9424/live
Dossier: https://lovarch.com/admin/squad-execution/5d585486-0991-4598-b880-171682ea9424/dossier

Project folder: ~/projects/attico-brera/
```
