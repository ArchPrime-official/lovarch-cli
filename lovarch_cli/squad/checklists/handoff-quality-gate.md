# Handoff Quality Gate · Squad Architettura-Progetto

> **Used by:** `@progetto-chief` at `step_4_receive_output` of the orchestration_protocol.
> **Triggered by:** `*receive` command after a specialist returns work.
> **Outcome:** PASS (route to QA) | REJECT (return to specialist) | ESCALATE (protocol violation).

This checklist enforces hub-and-spoke topology and the cerimônia de retorno.
Skipping any blocking check is a constitutional violation (AP-PP-001).

---

## SECTION 1 · Protocol Integrity (BLOCKING)

These enforce the hub-and-spoke rule. Failure = protocol violation.

| # | Check | Pass Criteria | Fail Action |
|---|-------|---------------|-------------|
| **P1** | **Announcement received** | Inbound card contains literally `"Retornando ao @progetto-chief. {trabalho} concluído."` | REJECT — return to specialist demanding announcement |
| **P2** | **No direct chaining** | Specialist did NOT route work directly to another specialist; output came back to hub | ESCALATE — log AP-VIOLATION-001, force re-routing |
| **P3** | **Cycle ID matches** | Inbound card's `cycle_id` matches outbound card's `cycle_id` | REJECT — request resubmission with correct ID |
| **P4** | **Specialist identity** | `from:` in inbound matches the specialist routed | ESCALATE — possible identity confusion, halt |
| **P5** | **Tier respect** | Tier 1 specialist did NOT skip Tier 2 QA before consolidation | ESCALATE — log AP-VIOLATION-002 |

**Section 1 verdict:** All 5 must PASS. Any FAIL halts the cycle.

---

## SECTION 2 · Output Completeness (BLOCKING)

| # | Check | Pass Criteria | Fail Action |
|---|-------|---------------|-------------|
| **O1** | **Files Created listed** | Inbound card includes `outputs.files_created` array (can be empty, but key must exist) | REJECT — request complete list |
| **O2** | **Change Log present** | 2-4 sentences describing what changed and why | REJECT — request meaningful change log |
| **O3** | **Convention Verification Report** | Each convention in outbound card is addressed (✓ or N/A with reason) | REJECT — request explicit verification |
| **O4** | **Deploy coordination flagged** | If `supabase/functions/` modified, `deploy_required: true` is explicit | REJECT — clarify deploy status |
| **O5** | **Suggested Next Step** | One of: Done / Multi-domain → next / Re-review — selected | REJECT — request explicit decision |
| **O6** | **QA self-check provided** | `qa_pre_check` populated with self-check counts | REJECT — request self-check |
| **O7** | **SHA256 + MIME for files** | Each file in `files_created` has SHA256 hash and MIME type | REJECT — incomplete file metadata |

**Section 2 verdict:** All 7 must PASS for clean return.

---

## SECTION 3 · Convention Compliance (BLOCKING per applicability)

Run only conventions flagged in outbound card. Box marked applicable but not respected = REJECT.

| # | Convention | Check | Source of truth |
|---|-----------|-------|-----------------|
| **C1** | UNI ISO 5457 format | DXF/PDF tavole in A1 with margini + cartiglio CNAPPC | architettura-progetto-rules.md §3.1 |
| **C2** | UNI ISO 128-1 line weights | Spessori 0.13/0.18/0.25/0.35/0.50/0.70 mm | rules.md §3.2 |
| **C3** | Layer ISO standard | DXF has CAD-A-WALL, CAD-A-DIM, etc. | rules.md §3.3 |
| **C4** | Tolerance ±1mm | All quotes verifiable to ±1mm | rules.md §3.5 |
| **C5** | UNI 11337-7 capitolato | Capitolato follows part 7 structure | rules.md §2.5 |
| **C6** | CAM 2025 ≥80% | Materials list ≥80% CAM-compliant | rules.md §2.6 |
| **C7** | DPR 380 article exists | Cited articles exist on Normattiva | rules.md §2.1 |
| **C8** | NTC 2018 cap 8.x correct | Classification matches intervention | rules.md §2.3 |
| **C9** | CSP/CSE evaluated | If multi-impresa, CSP/CSE flagged | rules.md §2.4 |
| **C10** | L.49/2023 equo compenso | Onorari ≥ DM 17/06/2016 parameters | rules.md §2.9 |
| **C11** | GDPR clauses present | Privacy info in contracts | rules.md §2.11 |
| **C12** | Italian primary language | Tecnici in italiano | rules.md §5.4 |
| **C13** | DS V8 standard | Presentazione cliente uses Lovarch DS V8 | (Lovarch CLAUDE.md) |
| **C14** | Naming convention | Files follow {NN}-{categoria}-{nome}.{ext} | rules.md §5.1 |
| **C15** | Banner "BOZZA" present | Files requiring human signature have banner | rules.md §5.5 |

**Section 3 verdict:** Each applicable check must PASS. Non-applicable skipped.

---

## SECTION 4 · QA Routing Decision (REQUIRED)

After Sections 1-3 PASS, chief decides which QA agents validate this output.

| # | QA Agent | Trigger Condition |
|---|---------|-------------------|
| **Q1** | `@quality-misure` | Output contains DXF, IFC, or numeric measurements (sup, vol, quote) |
| **Q2** | `@quality-normativa` | Output contains normative references (DPR 380, UNI, CAM, NTC, paesaggistica) |
| **Q3** | `@quality-dati` | Output contains data points that must match other documents (totals, addresses, IDs) |
| **Q4** | `@quality-output` | ALWAYS (mandatory for any deliverable) |

**Min QA agents required:** 2 (always Q4 + at least one of Q1-Q3 based on content).

---

## SECTION 5 · Status Machine Update (REQUIRED)

| # | Check | Pass Criteria | Fail Action |
|---|-------|---------------|-------------|
| **S1** | Status transitioned correctly | Routed → InProgress → Returned → (now QA_Pending) | Update status, do not block |
| **S2** | CHANGELOG.md will be updated | Cycle outcome will be appended on Done | Chief responsibility on PASS |
| **S3** | pm_squad_steps row updated | Supabase row reflects new status | Auto-handled by simulator/squad |

---

## SECTION 6 · Multi-Domain Handoff (CONDITIONAL)

If cycle is multi-domain (involves 2+ specialists in sequence):

| # | Check | Pass Criteria |
|---|-------|---------------|
| **M1** | Previous specialist's output is in next specialist's context | Outbound card to next quotes prior `files_created` + `change_log` |
| **M2** | Sequence is serial, not parallel | No 2 specialists working concurrently on same cycle |
| **M3** | Each output passed Sections 1-3 individually | Verified by chief between routings |
| **M4** | QA validation between Tier 1 outputs | Each major output passes through min 2 QA agents |

---

## VERDICT FORMAT

After running checklist, chief produces:

```markdown
## Handoff Quality Gate · Cycle {Cycle ID}

**Specialist:** @{specialist}
**Verdict:** PASS | REJECT | ESCALATE

### Section Scores
- Section 1 (Protocol):     {n/5 PASS}
- Section 2 (Completeness): {n/7 PASS}
- Section 3 (Conventions):  {n applicable, m PASS}
- Section 4 (QA Routing):   Routed to: [@quality-X, @quality-Y]
- Section 5 (Status):       PASS
- Section 6 (Multi-domain): N/A | {n/4 PASS}

### Failures (if any)
- [ID]: {description} → {required action}

### Next Action
- PASS  → step_5: route to QA agents [list]
- REJECT → return to @{specialist} with feedback
- ESCALATE → log AP-VIOLATION-{nnn}, halt cycle, notify Pablo
```

---

## VERDICT EXAMPLES

### Example 1 · Clean PASS

```markdown
## Handoff Quality Gate · Cycle a7f4b2e1

**Specialist:** @cad-engineer
**Verdict:** PASS

### Section Scores
- Section 1 (Protocol):     5/5 PASS
- Section 2 (Completeness): 7/7 PASS
- Section 3 (Conventions):  C1, C2, C3, C4 applicable · 4/4 PASS
- Section 4 (QA Routing):   Routed to: @quality-misure, @quality-output
- Section 5 (Status):       PASS

### Next Action
PASS → step_5: route to @quality-misure (priority) + @quality-output
```

### Example 2 · REJECT

```markdown
## Handoff Quality Gate · Cycle b8e5c3f2

**Specialist:** @capitolato-writer
**Verdict:** REJECT

### Section Scores
- Section 1 (Protocol):     5/5 PASS
- Section 2 (Completeness): 5/7 (O3, O7 FAIL)
- Section 3 (Conventions):  C5, C6 applicable · 1/2 (C6 FAIL)

### Failures
- [O3]: Convention C6 (CAM 2025 ≥80%) marked applicable but not addressed in report
- [O7]: SHA256 missing for capitolato-speciale.pdf
- [C6]: Lista materiali non riporta voci CAM rispettati (solo 60% CAM-compliant)

### Next Action
REJECT → return to @capitolato-writer with feedback above
```

### Example 3 · ESCALATE

```markdown
## Handoff Quality Gate · Cycle c9f6d4g3

**Specialist:** @bim-engineer
**Verdict:** ESCALATE

### Section Scores
- Section 1 (Protocol):     3/5 (P2, P5 FAIL)
- Section 2 (Completeness): 7/7 PASS

### Failures
- [P2]: @bim-engineer routed output directly to @computo-engineer → AP-VIOLATION-001
- [P5]: @bim-engineer skipped @quality-misure → AP-VIOLATION-002

### Next Action
ESCALATE → log violation, halt cycle, notify Pablo
Repeated violations require squad architecture review.
```

---

## ENFORCEMENT NOTES

- This checklist is **executed by @progetto-chief**, not the specialist.
- Chief MUST run it before transitioning Returned → QA_Pending.
- A passed gate is the only path to status `QA_Pending`. No shortcuts.
- Repeated REJECT on same specialist (>2 in a cycle) escalates to user with diagnostic.
- ESCALATE outcomes logged in `data/CHANGELOG.md` with `[AP-VIOLATION-{nnn}]` prefix.

---

## VIOLATION CODES

| Code | Description |
|------|-------------|
| `AP-VIOLATION-001` | Specialist-to-specialist direct chaining |
| `AP-VIOLATION-002` | Tier 1 → consolidation skipping Tier 2 QA |
| `AP-VIOLATION-003` | Output without required announcement |
| `AP-VIOLATION-004` | Cycle ID mismatch |
| `AP-VIOLATION-005` | Identity confusion (from ≠ routed specialist) |
| `AP-VIOLATION-006` | Convention C6 violated (CAM 2025 <80%) without justification |
| `AP-VIOLATION-007` | Convention C4 violated (tolerance >1mm) without justification |
| `AP-VIOLATION-008` | Repeated REJECT (>3 retries) without escalation |
| `AP-VIOLATION-009` | Modified central document `architettura-progetto-rules.md` without ECR |
| `AP-VIOLATION-010` | Missing CHANGELOG.md update after Done |

---

**Pattern reference:** AP-PP-001 (Hub-and-Spoke Handoff)
**Enforced by:** @progetto-chief at every handoff cycle
**Source:** `data/architettura-progetto-rules.md` §1.1
