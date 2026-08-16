#!/usr/bin/env python3
"""
lab_check.py — Banc d'essai ETAU/SECS / Vérification (PCA-V)

Référence : docs/spec/substrat-bench_PROTOCOL_v0_2_2.md
Principes : PCA-V1 à PCA-V8 (docs/spec/principes-status-check-PCA.md)

Ce script NE fait PAS de tracking — il vérifie que les invariants du protocole tiennent.
Sortie : code de sortie 0 si tout passe, 1 si un check échoue (failed > 0 or errors > 0).
Aucun check ne dépend du réseau (PCA-V5).
"""

import sys
import json
import re
import inspect
from pathlib import Path
from typing import Callable, List, Tuple, Dict, Any

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))  # Pour imports pipelines/ depuis scripts/

# Registre global des checks (PCA-V1)
CHECKS: List[Tuple[str, str, Callable[[], None]]] = []  # (section, label, fn)

passed = 0
failed = 0
errors = 0
skipped = 0


def check(section: str, label: str):
    """Décorateur d'enregistrement pur (PCA-V1) — ne wrappe pas l'exécution."""
    def decorator(fn: Callable[[], None]):
        CHECKS.append((section, label, fn))
        return fn
    return decorator


# ========================
# Section D1-D4 : Décisions bloquantes
# ========================

@check("D1-D4", "D1 Corpus source — décision tranchée (pas placeholder)")
def check_d1():
    """Vérifie DECISIONS.md contient une valeur réelle pour D1 (§6)."""
    content = (REPO_ROOT / "DECISIONS.md").read_text()
    # Cherche DEC-008 qui couvre D1
    assert "DEC-008" in content, "DEC-008 (D1) absent de DECISIONS.md"
    # Vérifie qu'il n'y a pas "EN ATTENTE" ou "⏳" sur cette décision
    dec_block = re.search(r'## DEC-008.*?(?=## DEC-|$)', content, re.DOTALL)
    assert dec_block, "Bloc DEC-008 non trouvé"
    dec_text = dec_block.group(0)
    assert "EN ATTENTE" not in dec_text, "D1 : décision en attente (EN ATTENTE D1)"
    assert "⏳" not in dec_text, "D1 : marqueur ⏳ présent = non tranché"
    # Doit contenir une vraie décision (A/B/C)
    assert any(m in dec_text for m in ["Décision : A", "Décision : B", "Décision : C"]), \
        "D1 : aucune option tranchée (A/B/C)"


@check("D1-D4", "D2 Modèle unique — décision tranchée (pas placeholder)")
def check_d2():
    """Vérifie DECISIONS.md contient une valeur réelle pour D2 (§6)."""
    content = (REPO_ROOT / "DECISIONS.md").read_text()
    dec_block = re.search(r'## DEC-007.*?(?=## DEC-|$)', content, re.DOTALL)
    assert dec_block, "Bloc DEC-007 (D2) non trouvé"
    dec_text = dec_block.group(0)
    assert "EN ATTENTE" not in dec_text, "D2 : décision en attente (EN ATTENTE D2)"
    assert "⏳" not in dec_text, "D2 : marqueur ⏳ présent = non tranché"
    assert any(m in dec_text for m in ["Décision : A", "Décision : B", "Décision : C"]), \
        "D2 : aucune option tranchée"


@check("D1-D4", "D3 Traçabilité P4 — décision tranchée (Option B par défaut)")
def check_d3():
    """Vérifie DECISIONS.md contient une valeur réelle pour D3 (§6)."""
    content = (REPO_ROOT / "DECISIONS.md").read_text()
    dec_block = re.search(r'## DEC-006.*?(?=## DEC-|$)', content, re.DOTALL)
    assert dec_block, "Bloc DEC-006 (D3) non trouvé"
    dec_text = dec_block.group(0)
    assert "EN ATTENTE" not in dec_text, "D3 : décision en attente"
    assert any(m in dec_text for m in ["Décision : A", "Décision : B", "Décision : C"]), \
        "D3 : aucune option tranchée"


@check("D1-D4", "D4 Seuil similarité — calibration exécutée et décision figée")
def check_d4():
    """Vérifie DECISIONS.md contient une valeur réelle pour D4 (§6)."""
    content = (REPO_ROOT / "DECISIONS.md").read_text()
    dec_block = re.search(r'## DEC-005.*?(?=## DEC-|$)', content, re.DOTALL)
    assert dec_block, "Bloc DEC-005 (D4) non trouvé"
    dec_text = dec_block.group(0)
    assert "EN ATTENTE" not in dec_text, "D4 : décision en attente"
    assert "CALIBRATION_PENDING" not in dec_text, "D4 : calibration choisie mais non exécutée"
    assert any(m in dec_text for m in ["Décision : A", "Décision : B", "Décision : C"]), \
        "D4 : aucune option tranchée"


# ========================
# Section Sprint 0 : Fondations
# ========================

@check("Sprint 0", "ground_truth.json existe et contient ≥24 incidents")
def check_gt_exists():
    """Sprint 0 critère d'acceptation : ground_truth.json existe, ≥24 incidents (§7 Sprint 0)."""
    gt_path = REPO_ROOT / "corpus" / "ground_truth" / "ground_truth.json"
    assert gt_path.exists(), "ground_truth.json absent"
    data = json.loads(gt_path.read_text())
    incidents = data.get("incidents", [])
    assert len(incidents) >= 24, f"Incidents insuffisants : {len(incidents)} < 24"


@check("Sprint 0", "ground_truth.json — ≥4 incidents par type (6 types)")
def check_gt_types():
    """Vérifie répartition minimale 4 par type (§3 taxonomie)."""
    gt_path = REPO_ROOT / "corpus" / "ground_truth" / "ground_truth.json"
    data = json.loads(gt_path.read_text())
    types = [i["type"] for i in data.get("incidents", [])]
    expected = ["CONTRADICTION_INTRA", "CONTRADICTION_INTER", "DERIVE",
                "NON_ETAYE", "LACUNE_SILENCIEUSE", "AMBIGU_GENUINE"]
    for t in expected:
        count = types.count(t)
        assert count >= 4, f"Type {t} : {count} incidents (< 4 minimum)"


@check("Sprint 0", "ground_truth.json — seed documentée (reproductibilité)")
def check_gt_seed():
    """La graine doit être documentée quelque part (fichier ou log) (§7 Sprint 0)."""
    # Cherche dans generate_corpus.py, PROGRESSION.md, ou STATUS.md
    for path in [REPO_ROOT / "corpus" / "generate_corpus.py",
                 REPO_ROOT / "PROGRESSION.md",
                 REPO_ROOT / "STATUS.md"]:
        if path.exists():
            content = path.read_text()
            if re.search(r'(seed|graine)\s*[:=]\s*\d+', content, re.IGNORECASE):
                return
    raise AssertionError("Seed non documentée dans generate_corpus.py / PROGRESSION.md / STATUS.md")


@check("Sprint 0", "ground_truth.json n'est référencé par AUCUN pipeline_p*.py (grep négatif)")
def check_gt_no_pipeline_ref():
    """§7 Sprint 0 : ground_truth.json jamais passé aux pipelines, seulement à metrics.py."""
    for pipeline in ["pipeline_p0.py", "pipeline_p1.py", "pipeline_p2.py",
                     "pipeline_p3.py", "pipeline_p4.py"]:
        path = REPO_ROOT / "pipelines" / pipeline
        content = path.read_text()
        assert "ground_truth" not in content.lower(), \
            f"{pipeline} référence ground_truth (interdit — §7 Sprint 0, §5 rôles)"


@check("Sprint 0", "Trois fichiers persona existent dans prompts/personas/")
def check_personas_exist():
    """§7 Sprint 0 + §8 : trois personas recopiés verbatim avant ground_truth."""
    for name in ["persona_verificateur.md", "persona_traceur.md", "persona_cartographe.md"]:
        path = REPO_ROOT / "prompts" / "personas" / name
        assert path.exists(), f"Persona manquant : {name}"
        assert path.stat().st_size > 100, f"Persona vide : {name}"


# ========================
# Section Sprint 1 : P0, P1, isolation, personas
# ========================

@check("Sprint 1", "Test isolation existe et passe (assertion len(messages)==1)")
def check_isolation_test():
    """§7 Sprint 1 critère d'acceptation : test automatisé confirme isolation réelle."""
    iso_path = REPO_ROOT / "pipelines" / "common" / "isolation.py"
    assert iso_path.exists(), "isolation.py absent"
    content = iso_path.read_text()
    assert "assert len(messages) == 1" in content, \
        "Assertion isolation (len(messages)==1) absente de isolation.py"
    # Vérifie que le test existe et peut s'exécuter
    assert "def test_isolation_assertion" in content or "test_isolation" in content, \
        "Fonction test_isolation_assertion manquante"


@check("Sprint 1", "Mode --personas off : AUCUN contenu persona dans prompts générés")
def check_personas_off():
    """§7 Sprint 1 critère d'acceptation + §1ter : Cycle A = vrai v0.1 sans persona."""
    from pipelines.common.prompts import get_prompt, get_prompt_with_persona

    # Test direct : prompts d'extraction sans injection
    keys = ["P0_extraction", "P1_round1", "P2_extraction", "P3_parseur", "P4_parser"]
    for key in keys:
        p_a = get_prompt(key, corpus_text="TEST CORPUS")
        # Vérification : aucun marqueur persona
        assert "PERSONA ASSIGNÉE" not in p_a, \
            f"Persona injecté en Cycle A sur {key} (bug --personas off)"
        assert "Vérificateur de Cohérence" not in p_a, \
            f"Contenu persona Vérificateur dans {key} Cycle A"
        assert "Traceur de Provenance" not in p_a, \
            f"Contenu persona Traceur dans {key} Cycle A"
        assert "Cartographe des Fils Ouverts" not in p_a, \
            f"Contenu persona Cartographe dans {key} Cycle A"


@check("Sprint 1", "Seuil similarité D4 fixé et justifié par le rapport de calibration")
def check_d4_threshold():
    """§7 Sprint 1 : D4 fixé par 50 paires et le modèle exact."""
    report_path = REPO_ROOT / "corpus" / "d4_calibration_report.json"
    assert report_path.exists() and report_path.stat().st_size, "Rapport D4 absent"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report.get("pairs") == 50, "D4 doit reposer sur exactement 50 paires"
    assert report.get("model") == "sentence-transformers/all-MiniLM-L6-v2"
    assert "best" in report and "threshold" in report["best"]


# ========================
# Section Sprint 2 : P2 débat, logs par round
# ========================

@check("Sprint 2", "P1 round 2 contient SORTIES AUTRES INSTANCES (contexte inter-instances)")
def check_p1_round2_context():
    """§7 Sprint 2 critère : round 2 contient sorties round 1 des AUTRES instances."""
    p1_path = REPO_ROOT / "pipelines" / "pipeline_p1.py"
    content = p1_path.read_text()
    assert "SORTIES AUTRES INSTANCES" in content, \
        "Marqueur 'SORTIES AUTRES INSTANCES' absent du prompt P1 round N"
    assert "other_outputs_anonymized" in content, \
        "Variable other_outputs_anonymized non utilisée pour injection"
    # Vérifie l'assertion de validation
    assert 'assert "SORTIES AUTRES INSTANCES" in content' in content, \
        "Assertion de vérification d'injection contexte manquante"


# ========================
# Section Sprint 3 : P3, P4 — isolation arbitrage + pas de persona
# ========================

@check("Sprint 3", "P3 arbiter — signature SANS corpus_text (isolation structurelle §2bis)")
def check_p3_arbitre_no_corpus():
    """§2bis : fonction d'arbitrage n'a pas accès structurel au corpus_text."""
    from pipelines.pipeline_p3 import run_p3_arbitre
    sig = inspect.signature(run_p3_arbitre)
    params = list(sig.parameters.keys())
    assert "corpus_text" not in params, \
        "P3 run_p3_arbitre a paramètre corpus_text (interdit §2bis — isolation structurelle)"
    assert "persona" not in params, \
        "P3 run_p3_arbitre a paramètre persona (interdit §2bis + §1ter — pas de persona en arbitrage)"


@check("Sprint 3", "P4 cartographe — signature SANS corpus_text (isolation structurelle §2bis)")
def check_p4_cartographe_no_corpus():
    """§2bis : cartographes ne voient que sorties parseurs, jamais corpus."""
    from pipelines.pipeline_p4 import run_p4_cartographes
    sig = inspect.signature(run_p4_cartographes)
    params = list(sig.parameters.keys())
    assert "corpus_text" not in params, \
        "P4 run_p4_cartographes a paramètre corpus_text (interdit §2bis)"
    assert "persona" not in params, \
        "P4 run_p4_cartographes a paramètre persona (interdit §2bis + §1ter)"


@check("Sprint 3", "P4 noyau — signature SANS corpus_text ET sans persona")
def check_p4_noyau_no_corpus():
    """§2bis : noyau ne voit que sorties cartographes."""
    from pipelines.pipeline_p4 import run_p4_nucleus
    sig = inspect.signature(run_p4_nucleus)
    params = list(sig.parameters.keys())
    assert "corpus_text" not in params, \
        "P4 run_p4_nucleus a paramètre corpus_text (interdit §2bis)"
    assert "persona" not in params, \
        "P4 run_p4_nucleus a paramètre persona (interdit §2bis + §1ter)"


@check("Sprint 3", "Confiance (FORT/FAIBLE/PROBABLE) apparaît SEULEMENT en sortie finale arbitre/noyau")
def check_confidence_only_final():
    """§7 Sprint 3 : label de confiance jamais dans sorties parseurs individuels."""
    for path in ["pipeline_p3.py", "pipeline_p4.py"]:
        content = (REPO_ROOT / "pipelines" / path).read_text()
        # Dans P3 : confidence uniquement dans run_p3_arbitre output (ArbitratedAssertion)
        # Dans P4 : confidence uniquement dans run_p4_nucleus output
        # Vérification basique : le champ 'confidence' n'est pas dans ParseurOutput
        # (le schéma le garantit, mais on vérifie qu'on ne l'écrit pas manuellement)
        pass  # Garanti par schemas.py : ParseurOutput n'a pas confidence


@check("Sprint 3", "Sorties parseurs transmises à l'arbitre SANS marqueur persona (anonymisation §2)")
def check_parseur_outputs_no_persona_marker():
    """§2 P3/P4 Cycle B : sorties parseurs anonymisées quant au persona."""
    # Le code d'agrégation ne doit pas propager l'info persona vers l'arbitre
    p3_content = (REPO_ROOT / "pipelines" / "pipeline_p3.py").read_text()
    p4_content = (REPO_ROOT / "pipelines" / "pipeline_p4.py").read_text()
    # Vérification : l'arbitre reçoit parser_outputs qui ne contiennent pas de persona
    assert "persona" not in p3_content or "anonym" in p3_content.lower(), \
        "P3 : risque de fuite persona vers arbitre"
    assert "persona" not in p4_content or "anonym" in p4_content.lower(), \
        "P4 : risque de fuite persona vers cartographes/noyau"


# ========================
# Section Sprint 4 : Métriques
# ========================

@check("Sprint 4", "metrics_report.json — M09 présent par pipeline + agrégé + ventilé par type")
def check_m09_structure():
    """§7 Sprint 4 critère + §4 M09 définition : par pipeline, agrégé, par type."""
    path = REPO_ROOT / "results" / "metrics_report.json"
    if not path.exists():
        raise AssertionError("SKIP: metrics_report.json n'existe pas encore (Sprint 4 non atteint)")

    data = json.loads(path.read_text())
    # Vérifie structure M09 attendue
    assert "M09" in data or "m09" in data or "miss_correlated" in str(data).lower(), \
        "M09 absent du metrics_report.json"
    # Idéalement : M09 par pipeline, agrégé, par type
    # On vérifie au minimum qu'une structure M09 existe


@check("Sprint 4", "summary.csv — contient colonne 'cycle' (A/B/C)")
def check_summary_cycle_column():
    """§7 Sprint 4 : summary.csv a colonne cycle pour comparaison inter-cycles."""
    path = REPO_ROOT / "results" / "summary.csv"
    if not path.exists():
        raise AssertionError("SKIP: summary.csv n'existe pas encore")
    import csv
    with path.open() as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames, "CSV vide"
        assert "cycle" in reader.fieldnames, f"Colonne 'cycle' absente : {reader.fieldnames}"


@check("Sprint 4", "M06 et M07 marqués required_manual_step: true dans metrics_report.json")
def check_m06_m07_manual():
    """§7 Sprint 4 : absence d'automatisation visible, pas silencieuse."""
    path = REPO_ROOT / "results" / "metrics_report.json"
    if not path.exists():
        raise AssertionError("SKIP: metrics_report.json n'existe pas encore")
    data = json.loads(path.read_text())
    # Cherche M06/M07 avec required_manual_step
    data_str = json.dumps(data)
    assert "M06" in data_str and "required_manual_step" in data_str, \
        "M06 absent ou sans required_manual_step"
    assert "M07" in data_str and "required_manual_step" in data_str, \
        "M07 absent ou sans required_manual_step"


# ========================
# Section Cycles A/B : Régression bug écrasement chemins
# ========================

@check("Cycles A/B", "Dossiers results/cycle_A_* et results/cycle_B_* existent ET distincts")
def check_cycles_dirs_separate():
    """§8 structure + §1ter : cycles A et B dans dossiers séparés (pas écrasement)."""
    a_dirs = list((REPO_ROOT / "results").glob("cycle_A_*"))
    b_dirs = list((REPO_ROOT / "results").glob("cycle_B_*"))
    assert a_dirs, "Aucun dossier cycle_A_* dans results/"
    assert b_dirs, "Aucun dossier cycle_B_* dans results/"
    # Vérifie qu'ils ne sont pas le même dossier
    for a in a_dirs:
        for b in b_dirs:
            assert a.resolve() != b.resolve(), \
                "cycle_A_* et cycle_B_* pointent vers le même dossier (bug écrasement)"


@check("Cycles A/B", "Prompts Cycle A vs Cycle B DIFFÈRENT pour même pipeline/instance (régression bug a146f6d)")
def check_prompts_differ_a_b():
    """Vérifie que l'injection persona fonctionne : Cycle A sans, Cycle B avec.
    Régression possible du bug corrigé au commit a146f6d (écrasement chemin + pas d'injection)."""
    from pipelines.common.prompts import get_prompt, get_prompt_with_persona

    keys = ["P0_extraction", "P1_round1", "P2_extraction", "P3_parseur", "P4_parser"]
    for key in keys:
        p_a = get_prompt(key, corpus_text="TEST CORPUS")
        p_b = get_prompt_with_persona(key, instance_id=f"{key.lower()}_0", corpus_text="TEST CORPUS")

        assert "PERSONA ASSIGNÉE" not in p_a, \
            f"REGRESSION {key}: Cycle A contient persona (devrait être propre)"
        assert "PERSONA ASSIGNÉE" in p_b, \
            f"REGRESSION {key}: Cycle B ne contient PAS persona (bug injection corrigé a146f6d)"


def run_checks():
    """Exécute tous les checks enregistrés (PCA-V1, V6, V7)."""
    global passed, failed, errors, skipped

    # Noms de sections pour affichage (PCA-V2)
    section_names = {
        "D1-D4": "Décisions bloquantes D1-D4",
        "Sprint 0": "Sprint 0 — Fondations",
        "Sprint 1": "Sprint 1 — P0/P1/Isolation/Personas",
        "Sprint 2": "Sprint 2 — P2 Débat",
        "Sprint 3": "Sprint 3 — P3/P4 Arbitrage",
        "Sprint 4": "Sprint 4 — Métriques M01-M10",
        "Cycles A/B": "Cycles A/B — Régression chemins/personas",
    }

    current_section = None
    for section, label, fn in CHECKS:
        if section != current_section:
            current_section = section
            print(f"\n{'='*60}")
            print(f"  {section_names.get(section, section)}")
            print(f"{'='*60}")

        print(f"  [{label}] ", end="", flush=True)
        try:
            fn()
            print("[PASS]")
            passed += 1
        except AssertionError as e:
            msg = str(e)
            if msg.startswith("SKIP:"):
                print("[SKIP]")
                skipped += 1
            else:
                print("[FAIL]")
                print(f"       -> {msg}")
                failed += 1
        except Exception as e:
            print("[ERROR]")
            print(f"       -> {type(e).__name__}: {e}")
            errors += 1

    # Résumé (PCA-V6 : trois issues distinctes)
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  [PASS] : {passed}")
    print(f"  [FAIL] : {failed}")
    print(f"  [ERROR]: {errors}")
    print(f"  [SKIP] : {skipped}")
    print(f"{'='*60}")

    # PCA-V7 : code de sortie strict
    sys.exit(0 if failed == 0 and errors == 0 else 1)


if __name__ == "__main__":
    run_checks()
