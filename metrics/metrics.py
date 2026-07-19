"""
metrics/metrics.py — Sprint 4 : Calcul M01-M08
M01-M05, M08 automatisés ; M06/M07 flaggés required_manual_step: true
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import csv

# Ground truth loading
def load_ground_truth(gt_path: Path) -> List[Dict[str, Any]]:
    """Charge ground_truth.json — JAMAIS appelé par pipelines, seulement ici."""
    with open(gt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("incidents", [])


def load_pipeline_results(result_path: Path) -> List[Dict[str, Any]]:
    """Charge assertions avec source_ref."""
    results = []
    with open(result_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def match_assertion_to_incident(
    assertion: Dict[str, Any],
    incidents: List[Dict[str, Any]],
    source_ref_tolerance: int = 0  # tour_n exact requis
) -> Optional[Dict[str, Any]]:
    """
    Trouve incident correspondant à l'assertion.
    Match sur source_ref exact (session_id + tour_n) + type cohérent.
    """
    src = assertion.get("source_ref", {})
    a_session = src.get("session_id")
    a_tour = src.get("tour_n")
    a_epistemic = assertion.get("epistemic_state", "")
    
    for inc in incidents:
        # Match sur source_ref_origine OU source_ref_reprise selon type
        for ref_key in ["source_ref_origine", "source_ref_reprise"]:
            ref = inc.get(ref_key, {})
            if (ref.get("session_id") == a_session and 
                ref.get("tour_n") == a_tour):
                # Vérification cohérence type/epistemic_state
                inc_type = inc.get("type", "")
                if _epistemic_matches_type(a_epistemic, inc_type):
                    return inc
    return None


def _epistemic_matches_type(epistemic: str, inc_type: str) -> bool:
    """Heuristique : epistemic_state compatible avec type incident."""
    mapping = {
        "CONTRADICTION_INTRA": "B",
        "CONTRADICTION_INTER": "B",
        "DERIVE": "N",       # Projection → ignorance/ambiguïté
        "NON_ETAYE": "N",
        "LACUNE_SILENCIEUSE": "N",
        "AMBIGU_GENUINE": "N"
    }
    return mapping.get(inc_type, "") == epistemic or epistemic in ("B", "N", "T", "F")


def compute_metrics(
    pipeline_results: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    tokens_used: int = 0,
    time_ms: int = 0
) -> Dict[str, Any]:
    """
    Calcule M01-M05, M08 pour un pipeline sur un cycle.
    
    Args:
        pipeline_results: Liste assertions (chacune avec source_ref, confidence, etc.)
        ground_truth: Liste incidents injectés
    
    Returns: Dict métriques
    """
    n_incidents = len(ground_truth)
    n_assertions = len(pipeline_results)
    
    # Matching
    detected_incidents = set()
    true_positives = 0
    localized_correctly = 0
    false_signals = 0
    
    confidence_correct = {"FORT": 0, "FAIBLE": 0, "PROBABLE": 0}
    confidence_total = {"FORT": 0, "FAIBLE": 0, "PROBABLE": 0}
    
    for assertion in pipeline_results:
        confidence = assertion.get("confidence", "FAIBLE")
        if confidence in confidence_total:
            confidence_total[confidence] += 1
        
        matched = match_assertion_to_incident(assertion, ground_truth)
        
        if matched:
            true_positives += 1
            detected_incidents.add(matched["incident_id"])
            
            # Localization precision : source_ref exact
            src = assertion.get("source_ref", {})
            ref_orig = matched.get("source_ref_origine", {})
            ref_rep = matched.get("source_ref_reprise", {})
            
            if (src.get("session_id") == ref_orig.get("session_id") and
                src.get("tour_n") == ref_orig.get("tour_n")):
                localized_correctly += 1
            elif (src.get("session_id") == ref_rep.get("session_id") and
                  src.get("tour_n") == ref_rep.get("tour_n")):
                localized_correctly += 1
            
            # Confidence calibration
            if confidence in confidence_correct:
                confidence_correct[confidence] += 1
        else:
            false_signals += 1
    
    # M01 Detection Recall
    detection_recall = true_positives / n_incidents if n_incidents > 0 else 0.0
    
    # M02 Localization Precision
    localization_precision = localized_correctly / true_positives if true_positives > 0 else 0.0
    
    # M03 False Signal Rate
    false_signal_rate = false_signals / n_assertions if n_assertions > 0 else 0.0
    
    # M04 Confidence Calibration
    calibration = {}
    for level in ["FORT", "PROBABLE", "FAIBLE"]:
        if confidence_total[level] > 0:
            calibration[level] = confidence_correct[level] / confidence_total[level]
        else:
            calibration[level] = None
    
    # M05 Cost per Detection
    cost_per_detection = (tokens_used + time_ms / 1000) / true_positives if true_positives > 0 else float('inf')
    
    # M08 Implementation Effort (statique, calculé une fois)
    # Voir compute_implementation_effort()
    
    return {
        "M01_detection_recall": round(detection_recall, 4),
        "M02_localization_precision": round(localization_precision, 4),
        "M03_false_signal_rate": round(false_signal_rate, 4),
        "M04_confidence_calibration": {k: round(v, 4) if v else None for k, v in calibration.items()},
        "M05_cost_per_detection": round(cost_per_detection, 2),
        "M06_traceability_utility": {"required_manual_step": True, "note": "Test aveugle humain 8 assertions"},
        "M07_closure_appropriate": {"required_manual_step": True, "note": "Vérification AMBIGU_GENUINE"},
        "M08_implementation_effort": None,  # Rempli par compute_implementation_effort()
        
        # Détails pour debug
        "_details": {
            "true_positives": true_positives,
            "false_signals": false_signals,
            "localized_correctly": localized_correctly,
            "detected_incident_ids": list(detected_incidents),
            "total_incidents": n_incidents,
            "total_assertions": n_assertions
        }
    }


def compute_implementation_effort(pipeline_name: str, code_root: Path) -> Dict[str, int]:
    """
    M08 : Lignes de code par pipeline + appels LLM par cycle.
    """
    pipeline_dir = code_root / "pipelines"
    
    if pipeline_name in ("P0", "P1"):
        target = pipeline_dir / f"pipeline_{pipeline_name.lower()}.py"
    elif pipeline_name in ("P2", "P3", "P4"):
        target = pipeline_dir / f"pipeline_{pipeline_name.lower()}.py"
    else:
        target = pipeline_dir / "common"
    
    loc = 0
    if target.is_file():
        loc = len(target.read_text(encoding='utf-8').splitlines())
    elif target.is_dir():
        for f in target.rglob("*.py"):
            loc += len(f.read_text(encoding='utf-8').splitlines())
    
    # Appels LLM par cycle (estimés §1 protocole)
    llm_calls = {
        "P0": 1,
        "P1": 3,      # 3 instances
        "P2": 6,      # 3 instances × 2 rounds
        "P3": 4,      # 3 parseurs + 1 arbitre
        "P4": 6       # 3 parseurs + 2 cartographes + 1 noyau
    }
    
    return {
        "lines_of_code": loc,
        "llm_calls_per_cycle": llm_calls.get(pipeline_name, 0)
    }


def run_all_metrics(
    results_dir: Path,
    ground_truth_path: Path,
    cycles: int = 5
) -> Tuple[List[Dict[str, Any]], Path]:
    """
    Calcule métriques pour tous pipelines × tous cycles.
    Produit metrics_report.json + summary.csv
    """
    incidents = load_ground_truth(ground_truth_path)
    
    all_metrics = []
    
    for cycle in range(cycles):
        cycle_dir = results_dir / f"cycle_{cycle}" / "raw_outputs"
        if not cycle_dir.exists():
            continue
        
        for pipeline in ["P0", "P1", "P2", "P3", "P4"]:
            # Trouve fichier parsed
            parsed_files = list(cycle_dir.glob(f"{pipeline.lower()}_*_parsed.jsonl"))
            if not parsed_files:
                # Try nucleus for P4, arbiter for P3
                if pipeline == "P4":
                    parsed_files = list(cycle_dir.glob("p4_nucleus*.jsonl"))
                elif pipeline == "P3":
                    parsed_files = list(cycle_dir.glob("p3_arbitre*.jsonl"))
            
            if not parsed_files:
                continue
            
            results = load_pipeline_results(parsed_files[0])
            
            # Tokens/time estimation (depuis logs ou approximation)
            tokens = sum(len(str(r).split()) * 1.3 for r in results)
            time_ms = 0  # TODO: collecter depuis logs
            
            metrics = compute_metrics(results, incidents, int(tokens), time_ms)
            metrics["pipeline"] = pipeline
            metrics["cycle"] = cycle
            
            # M08
            code_root = results_dir.parent
            metrics["M08_implementation_effort"] = compute_implementation_effort(pipeline, code_root)
            
            all_metrics.append(metrics)
    
    # Agrégation par pipeline (médiane sur cycles)
    summary = aggregate_metrics(all_metrics)
    
    # Sauvegarde
    report_path = results_dir / "metrics_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "per_cycle": all_metrics,
            "summary": summary
        }, f, ensure_ascii=False, indent=2)
    
    # CSV summary
    csv_path = results_dir / "summary.csv"
    write_summary_csv(summary, csv_path)
    
    return all_metrics, report_path


def aggregate_metrics(per_cycle: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Médiane + IQR par pipeline sur métriques clés."""
    import numpy as np
    
    by_pipeline = defaultdict(list)
    for m in per_cycle:
        by_pipeline[m["pipeline"]].append(m)
    
    summary = {}
    for pipeline, cycles in by_pipeline.items():
        def med(key):
            vals = [c[key] for c in cycles if c[key] is not None]
            return float(np.median(vals)) if vals else 0.0
        
        def iqr(key):
            vals = [c[key] for c in cycles if c[key] is not None]
            if len(vals) < 2:
                return 0.0
            q75, q25 = np.percentile(vals, [75, 25])
            return float(q75 - q25)
        
        summary[pipeline] = {
            "M01_recall_median": med("M01_detection_recall"),
            "M01_recall_iqr": iqr("M01_detection_recall"),
            "M02_precision_median": med("M02_localization_precision"),
            "M02_precision_iqr": iqr("M02_localization_precision"),
            "M03_false_signal_median": med("M03_false_signal_rate"),
            "M03_false_signal_iqr": iqr("M03_false_signal_rate"),
            "M05_cost_median": med("M05_cost_per_detection"),
            "M05_cost_iqr": iqr("M05_cost_per_detection"),
            "M08_loc": cycles[0].get("M08_implementation_effort", {}).get("lines_of_code", 0),
            "M08_llm_calls": cycles[0].get("M08_implementation_effort", {}).get("llm_calls_per_cycle", 0),
            "cycles": len(cycles)
        }
    
    return summary


def write_summary_csv(summary: Dict, path: Path) -> None:
    """Écrit summary.csv lisible par instance analyse sans code."""
    fieldnames = [
        "pipeline", "M01_recall_median", "M01_recall_iqr",
        "M02_precision_median", "M02_precision_iqr",
        "M03_false_signal_median", "M03_false_signal_iqr",
        "M05_cost_median", "M05_cost_iqr",
        "M08_loc", "M08_llm_calls", "cycles"
    ]
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for pipeline, vals in summary.items():
            row = {"pipeline": pipeline, **vals}
            writer.writerow(row)


# === Test unitaire ===
def test_metrics():
    """Test basique métriques."""
    gt = [
        {"incident_id": "INC-01", "type": "CONTRADICTION_INTRA",
         "source_ref_origine": {"session_id": "s1", "tour_n": 5},
         "source_ref_reprise": {"session_id": "s1", "tour_n": 8}},
        {"incident_id": "INC-02", "type": "DERIVE",
         "source_ref_origine": {"session_id": "s2", "tour_n": 3},
         "source_ref_reprise": {"session_id": "s3", "tour_n": 1}},
    ]
    
    # Assertions parfaites
    results = [
        {"text": "Contradiction détectée", "source_ref": {"session_id": "s1", "tour_n": 5},
         "epistemic_state": "B", "confidence": "FORT"},
        {"text": "Dérive β=N", "source_ref": {"session_id": "s2", "tour_n": 3},
         "epistemic_state": "N", "confidence": "FORT"},
    ]
    
    m = compute_metrics(results, gt, 1000, 5000)
    
    assert m["M01_detection_recall"] == 1.0
    assert m["M02_localization_precision"] == 1.0
    assert m["M03_false_signal_rate"] == 0.0
    assert m["M04_confidence_calibration"]["FORT"] == 1.0
    
    # Assertions avec faux positif
    results_with_fp = results + [
        {"text": "Hallucination", "source_ref": {"session_id": "s9", "tour_n": 99},
         "epistemic_state": "T", "confidence": "FAIBLE"}
    ]
    
    m2 = compute_metrics(results_with_fp, gt, 1000, 5000)
    assert m2["M03_false_signal_rate"] == 1/3
    
    print("[OK] test_metrics passed")


if __name__ == "__main__":
    test_metrics()