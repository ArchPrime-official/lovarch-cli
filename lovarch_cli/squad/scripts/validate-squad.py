"""
validate-squad.py · AIOS Quality Gate Validator

Runs squad-checklist v3.1 (Tier 1-4) against squad architettura-progetto
and outputs a quality score (target: 10/10).

Usage:
    python3 validate-squad.py [--verbose]

Exit codes:
    0 = PASS (score ≥7.0)
    1 = FAIL (score <7.0)
    2 = ERROR (validation crashed)
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


SQUAD_DIR = Path(__file__).parent.parent
VERBOSE = "--verbose" in sys.argv


# ============================================================================
# TIER 1 · STRUCTURE (BLOCKING)
# ============================================================================

def check_tier_1() -> Tuple[float, List[Dict]]:
    """Returns (score 0-10, list of check results)"""
    checks = []

    # 1.1 config.yaml exists + parseable
    config_path = SQUAD_DIR / "config.yaml"
    config_exists = config_path.exists()
    checks.append({"id": "1.1", "name": "config.yaml exists", "pass": config_exists, "severity": "BLOCKING"})

    config_text = config_path.read_text() if config_exists else ""

    # 1.1 Required fields
    required_fields = ["name:", "version:", "description:", "entry_agent:"]
    for field in required_fields:
        present = field in config_text
        checks.append({
            "id": f"1.1.{field}",
            "name": f"config field {field}",
            "pass": present,
            "severity": "BLOCKING",
        })

    # 1.1 author
    author_present = "author:" in config_text
    checks.append({"id": "1.1.author", "name": "config has author", "pass": author_present, "severity": "BLOCKING"})

    # 1.1 slashPrefix
    slash_present = "slashPrefix:" in config_text
    checks.append({"id": "1.1.slashPrefix", "name": "config has slashPrefix", "pass": slash_present, "severity": "BLOCKING"})

    # 1.4 Directory structure
    dirs = ["agents", "tasks", "checklists", "data", "templates", "workflows", "scripts"]
    for d in dirs:
        d_path = SQUAD_DIR / d
        exists = d_path.exists() and d_path.is_dir()
        checks.append({"id": f"1.4.{d}", "name": f"dir {d}/", "pass": exists, "severity": "BLOCKING"})

    # 1.4 Min agents count (>=1)
    agents_dir = SQUAD_DIR / "agents"
    agents_count = len(list(agents_dir.glob("*.md"))) if agents_dir.exists() else 0
    checks.append({
        "id": "1.4.agents_count",
        "name": f"agents count >=1 (actual: {agents_count})",
        "pass": agents_count >= 1,
        "severity": "BLOCKING",
    })

    # 1.4 Min tasks count (>=1 per AIOS standard)
    tasks_dir = SQUAD_DIR / "tasks"
    tasks_count = len(list(tasks_dir.glob("*.md"))) if tasks_dir.exists() else 0
    checks.append({
        "id": "1.4.tasks_count",
        "name": f"tasks count >=1 (actual: {tasks_count})",
        "pass": tasks_count >= 1,
        "severity": "BLOCKING",
    })

    # 1.5 Cross-references
    central_doc = SQUAD_DIR / "data" / "architettura-progetto-rules.md"
    central_exists = central_doc.exists()
    checks.append({"id": "1.5.central_doc", "name": "central document exists", "pass": central_exists, "severity": "BLOCKING"})

    changelog = SQUAD_DIR / "data" / "CHANGELOG.md"
    changelog_exists = changelog.exists()
    checks.append({"id": "1.5.changelog", "name": "CHANGELOG.md exists", "pass": changelog_exists, "severity": "BLOCKING"})

    handoff_card = SQUAD_DIR / "data" / "handoff-card-template.md"
    handoff_card_exists = handoff_card.exists()
    checks.append({"id": "1.5.handoff_card", "name": "handoff-card-template exists", "pass": handoff_card_exists, "severity": "BLOCKING"})

    handoff_qa = SQUAD_DIR / "checklists" / "handoff-quality-gate.md"
    handoff_qa_exists = handoff_qa.exists()
    checks.append({"id": "1.5.handoff_qa", "name": "handoff-quality-gate exists", "pass": handoff_qa_exists, "severity": "BLOCKING"})

    # 1.6 Security scan (no hardcoded secrets in YAML)
    secrets_pattern = re.compile(r"(api[_-]?key|secret|password)\s*[:=]\s*['\"][^'\"]{20,}", re.IGNORECASE)
    has_secrets = bool(secrets_pattern.search(config_text))
    checks.append({"id": "1.6.no_secrets", "name": "no hardcoded secrets", "pass": not has_secrets, "severity": "BLOCKING"})

    # Score
    total = len(checks)
    passed = sum(1 for c in checks if c["pass"])
    score = (passed / total) * 10
    return score, checks


# ============================================================================
# TIER 2 · COVERAGE (BLOCKING)
# ============================================================================

def check_tier_2() -> Tuple[float, List[Dict]]:
    checks = []

    # Tier 0 orchestrator exists
    chief_exists = (SQUAD_DIR / "agents" / "progetto-chief.md").exists()
    checks.append({"id": "2.1.chief", "name": "Tier 0 orchestrator exists", "pass": chief_exists, "severity": "BLOCKING"})

    # Auditor input
    auditor_exists = (SQUAD_DIR / "agents" / "auditor-input.md").exists()
    checks.append({"id": "2.2.auditor", "name": "auditor-input exists", "pass": auditor_exists, "severity": "BLOCKING"})

    # Tier 1 specialists ≥5
    tier1_agents = [
        "briefing-architect", "regolatorio-it", "concept-designer", "cad-engineer",
        "bim-engineer", "computo-engineer", "capitolato-writer", "pratiche-it",
        "contratto-architect", "energy-prelim", "deliverable-builder",
    ]
    tier1_present = sum(1 for a in tier1_agents if (SQUAD_DIR / "agents" / f"{a}.md").exists())
    checks.append({
        "id": "2.3.tier1_count",
        "name": f"Tier 1 specialists ≥5 (actual: {tier1_present})",
        "pass": tier1_present >= 5,
        "severity": "BLOCKING",
    })

    # Tier 2 QA agents
    qa_agents = ["quality-misure", "quality-normativa", "quality-dati", "quality-output"]
    qa_present = sum(1 for a in qa_agents if (SQUAD_DIR / "agents" / f"{a}.md").exists())
    checks.append({
        "id": "2.4.qa_count",
        "name": f"Tier 2 QA agents ≥4 (actual: {qa_present})",
        "pass": qa_present >= 4,
        "severity": "BLOCKING",
    })

    # Tasks ≥3 (atomic)
    tasks = list((SQUAD_DIR / "tasks").glob("*.md")) if (SQUAD_DIR / "tasks").exists() else []
    checks.append({
        "id": "2.5.tasks_count",
        "name": f"Tasks ≥3 (actual: {len(tasks)})",
        "pass": len(tasks) >= 3,
        "severity": "BLOCKING",
    })

    # Workflows ≥1
    workflows = list((SQUAD_DIR / "workflows").glob("*.yaml")) if (SQUAD_DIR / "workflows").exists() else []
    checks.append({
        "id": "2.6.workflows_count",
        "name": f"Workflows ≥1 (actual: {len(workflows)})",
        "pass": len(workflows) >= 1,
        "severity": "BLOCKING",
    })

    # Templates ≥3
    templates = list((SQUAD_DIR / "templates").glob("*.md")) if (SQUAD_DIR / "templates").exists() else []
    checks.append({
        "id": "2.7.templates_count",
        "name": f"Templates ≥3 (actual: {len(templates)})",
        "pass": len(templates) >= 3,
        "severity": "BLOCKING",
    })

    # Checklists ≥4 (1 handoff + 4 QA)
    checklists = list((SQUAD_DIR / "checklists").glob("*.md")) if (SQUAD_DIR / "checklists").exists() else []
    checks.append({
        "id": "2.8.checklists_count",
        "name": f"Checklists ≥5 (actual: {len(checklists)})",
        "pass": len(checklists) >= 5,
        "severity": "BLOCKING",
    })

    total = len(checks)
    passed = sum(1 for c in checks if c["pass"])
    score = (passed / total) * 10
    return score, checks


# ============================================================================
# TIER 3 · QUALITY (THRESHOLD 7.0)
# ============================================================================

REQUIRED_AGENT_SECTIONS = [
    "ACTIVATION-NOTICE",
    "IDE-FILE-RESOLUTION",
    "REQUEST-RESOLUTION",
    "activation-instructions",
    "command_loader",
    "agent:",
    "persona:",
    "core_principles",
    "voice_dna:",
    "thinking_dna:",
    "handoff_to:",
    "output_examples:",
    "anti_patterns:",
    "completion_criteria:",
    "smoke_tests:",
    "integration:",
    "greeting:",
]


def check_agent_quality(agent_path: Path) -> Tuple[float, List[Dict]]:
    """Per-agent AIOS 6-level structure check."""
    if not agent_path.exists():
        return 0, [{"id": "missing", "name": f"{agent_path.name} missing", "pass": False, "severity": "BLOCKING"}]

    content = agent_path.read_text()
    checks = []

    for section in REQUIRED_AGENT_SECTIONS:
        present = section in content
        checks.append({
            "id": f"agent.{section}",
            "name": f"{agent_path.name} has {section}",
            "pass": present,
            "severity": "QUALITY",
        })

    # Additional quality checks
    has_smoke_3 = content.count("test_") >= 3
    checks.append({"id": "agent.smoke_tests_3", "name": f"{agent_path.name} 3 smoke tests", "pass": has_smoke_3, "severity": "QUALITY"})

    has_examples_3 = len(re.findall(r"- input:", content)) >= 3
    checks.append({"id": "agent.examples_3", "name": f"{agent_path.name} 3 output examples", "pass": has_examples_3, "severity": "QUALITY"})

    has_source_traces = "[SOURCE:" in content or "[Deming" in content or "[Juran" in content or "[English" in content or "[Dodds" in content or "[Schumacher" in content or "[Baldwin" in content or "[Mazria" in content or "signature]" in content
    checks.append({"id": "agent.source_traces", "name": f"{agent_path.name} has [SOURCE:] traces", "pass": has_source_traces, "severity": "QUALITY"})

    total = len(checks)
    passed = sum(1 for c in checks if c["pass"])
    score = (passed / total) * 10
    return score, checks


def check_tier_3() -> Tuple[float, List[Dict]]:
    agents = list((SQUAD_DIR / "agents").glob("*.md"))
    all_checks = []
    scores = []

    for agent_path in agents:
        score, checks = check_agent_quality(agent_path)
        scores.append(score)
        all_checks.extend(checks)

    avg_score = sum(scores) / len(scores) if scores else 0
    return avg_score, all_checks


# ============================================================================
# TIER 4 · CONTEXTUAL (squad type)
# ============================================================================

def check_tier_4() -> Tuple[float, List[Dict]]:
    """Detect squad type · architettura-progetto = Hybrid (process + heuristics)"""
    checks = []
    config_text = (SQUAD_DIR / "config.yaml").read_text() if (SQUAD_DIR / "config.yaml").exists() else ""

    has_hub_spoke = "hub_and_spoke" in config_text
    checks.append({"id": "4.1.hub_spoke", "name": "Hub-and-spoke topology", "pass": has_hub_spoke, "severity": "QUALITY"})

    has_executor_types = "executor_types:" in config_text
    checks.append({"id": "4.2.executor_types", "name": "Executor types defined", "pass": has_executor_types, "severity": "QUALITY"})

    has_pattern_lib = "pattern_library:" in config_text
    checks.append({"id": "4.3.pattern_library", "name": "Pattern library defined", "pass": has_pattern_lib, "severity": "QUALITY"})

    has_quality_gates = "quality_gates:" in config_text
    checks.append({"id": "4.4.quality_gates", "name": "Quality gates referenced", "pass": has_quality_gates, "severity": "QUALITY"})

    # Mind clones traceable
    mind_clones = ["quality-misure", "quality-normativa", "quality-dati", "quality-output", "concept-designer", "bim-engineer", "energy-prelim"]
    clones_with_source = 0
    for c in mind_clones:
        cpath = SQUAD_DIR / "agents" / f"{c}.md"
        if cpath.exists() and "based_on:" in cpath.read_text():
            clones_with_source += 1
    checks.append({
        "id": "4.5.mind_clones",
        "name": f"Mind clones documented ({clones_with_source}/7)",
        "pass": clones_with_source >= 7,
        "severity": "QUALITY",
    })

    total = len(checks)
    passed = sum(1 for c in checks if c["pass"])
    score = (passed / total) * 10
    return score, checks


# ============================================================================
# RUNNER
# ============================================================================

def main():
    print("\n" + "=" * 70)
    print("  Squad Validation · architettura-progetto")
    print("  Applying squad-checklist v3.1 · AIOS Standard")
    print("=" * 70 + "\n")

    t1_score, t1_checks = check_tier_1()
    t2_score, t2_checks = check_tier_2()
    t3_score, t3_checks = check_tier_3()
    t4_score, t4_checks = check_tier_4()

    # Final score (weighted: T3 × 0.5 + T1 × 0.2 + T2 × 0.2 + T4 × 0.1)
    final = (t3_score * 0.5) + (t1_score * 0.2) + (t2_score * 0.2) + (t4_score * 0.1)

    print(f"Tier 1 · Structure:    {t1_score:5.2f}/10  ({sum(1 for c in t1_checks if c['pass'])}/{len(t1_checks)} checks)")
    print(f"Tier 2 · Coverage:     {t2_score:5.2f}/10  ({sum(1 for c in t2_checks if c['pass'])}/{len(t2_checks)} checks)")
    print(f"Tier 3 · Quality:      {t3_score:5.2f}/10  (per-agent average · {len(list((SQUAD_DIR/'agents').glob('*.md')))} agents)")
    print(f"Tier 4 · Contextual:   {t4_score:5.2f}/10  ({sum(1 for c in t4_checks if c['pass'])}/{len(t4_checks)} checks)")
    print(f"")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  FINAL SCORE:  {final:5.2f}/10")
    print(f"  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"")

    if final >= 9.0:
        print("  Verdict: EXCELLENCE 🏆")
    elif final >= 7.0:
        print("  Verdict: PASS ✓")
    else:
        print("  Verdict: FAIL ✗")
    print("")

    if VERBOSE:
        print("\n--- Tier 1 · Structure (BLOCKING) ---")
        for c in t1_checks:
            mark = "✓" if c["pass"] else "✗"
            print(f"  {mark} [{c['id']}] {c['name']}")

        print("\n--- Tier 2 · Coverage (BLOCKING) ---")
        for c in t2_checks:
            mark = "✓" if c["pass"] else "✗"
            print(f"  {mark} [{c['id']}] {c['name']}")

        # Tier 3 · group by agent
        print("\n--- Tier 3 · Quality (per agent) ---")
        agents = list((SQUAD_DIR / "agents").glob("*.md"))
        for agent_path in agents:
            score, checks = check_agent_quality(agent_path)
            print(f"  {agent_path.stem}: {score:.1f}/10  ({sum(1 for c in checks if c['pass'])}/{len(checks)})")

        print("\n--- Tier 4 · Contextual ---")
        for c in t4_checks:
            mark = "✓" if c["pass"] else "✗"
            print(f"  {mark} [{c['id']}] {c['name']}")

        # Failed only
        all_failed = [c for c in (t1_checks + t2_checks + t4_checks) if not c["pass"]]
        if all_failed:
            print(f"\n--- {len(all_failed)} FAILED CHECKS ---")
            for c in all_failed:
                print(f"  ✗ [{c['id']}] {c['name']}")

    if final >= 7.0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
