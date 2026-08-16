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
import sys

CODE_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(CODE_ROOT))
from pipelines.common.agregation import text_similarity
from pipelines.common.schemas import iter_json_objects


# Ground truth loading
def load_ground_truth(gt_path: Path) -> List[Dict[str, Any]]:
    """Charge ground_truth.json — JAMAIS appelé par pipelines, seulement ici."""
    with open(gt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("incidents", [])


def load_pipeline_results(result_path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Charge assertions avec source_ref."""
    results = []
    text = result_path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        values = json.loads(text)
        return values[:limit] if limit is not None else values
    return list(iter_json_objects(text, limit=limit))


def match_assertion_to_incident(
    assertion: Dict[str, Any],
    incidents: List[Dict[str, Any]],
    source_ref_tolerance: int = 0,  # tour_n exact requis
    similarity_threshold: float = 0.36,
    allow_lexical_fallback: bool = True,
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
                reference_text = inc.get("description_courte", "")
                similarity_ok = bool(reference_text) and text_similarity(
                    assertion.get("text", assertion.get("representative_text", "")), reference_text,
                    allow_lexical_fallback=allow_lexical_fallback,
                ) >= similarity_threshold
                if _epistemic_matches_type(a_epistemic, inc_type) and similarity_ok:
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
    return mapping.get(inc_type, "") == epistemic


def compute_metrics(
    pipeline_results: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    costs: Optional[Dict[str, Any]] = None,
    allow_lexical_fallback: bool = True,
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
        
        matched = match_assertion_to_incident(assertion, ground_truth,
                                               allow_lexical_fallback=allow_lexical_fallback)
        
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
    detection_recall = len(detected_incidents) / n_incidents if n_incidents > 0 else 0.0
    
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
    
    # M05 reste un vecteur : aucune addition d'unités incompatibles.
    costs = costs or {}
    def per_tp(name: str):
        value = costs.get(name)
        return (value / true_positives) if value is not None and true_positives else None
    cost_per_detection = {
        "llm_responses_per_tp": per_tp("llm_responses"),
        "input_tokens_per_tp": per_tp("input_tokens"),
        "output_tokens_per_tp": per_tp("output_tokens"),
        "wall_time_ms_per_tp": per_tp("wall_time_ms"),
        "estimated_cost_usd_per_tp": per_tp("estimated_cost_usd"),
    }
    
    # M08 Implementation Effort (statique, calculé une fois)
    # Voir compute_implementation_effort()
    
    return {
        "M01_detection_recall": round(detection_recall, 4),
        "M02_localization_precision": round(localization_precision, 4),
        "M03_false_signal_rate": round(false_signal_rate, 4),
        "M04_confidence_calibration": {k: round(v, 4) if v else None for k, v in calibration.items()},
        "M05_cost_per_detection": cost_per_detection,
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
        "P1": 6,      # 3 instances × 2 rounds
        "P2": 6,      # 6 lectures indépendantes imbriquées
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
    cycles: int = 5,
    cycle_labels: Tuple[str, ...] = ("A", "B"),
) -> Tuple[List[Dict[str, Any]], Path]:
    """
    Calcule métriques pour tous pipelines × tous cycles.
    Produit metrics_report.json + summary.csv
    """
    incidents = load_ground_truth(ground_truth_path)
    
    ledger_path = results_dir / "inference_ledger.jsonl"
    ledger = load_pipeline_results(ledger_path) if ledger_path.exists() else []
    allow_lexical_fallback = bool(ledger) and all(row.get("provider") == "mock" for row in ledger)
    all_metrics = []
    metric_index = {}

    for cycle_label in cycle_labels:
      for cycle in range(cycles):
        cycle_dir = results_dir / f"cycle_{cycle_label}_{cycle}" / "raw_outputs"
        if not cycle_dir.exists():
            continue
        result_files = {
            "P0": cycle_dir / f"p0_cycle{cycle}_parsed.jsonl",
            "P1": cycle_dir / f"p1_cycle{cycle}_retained.json",
            "P2@3": cycle_dir / f"p2_at3_cycle{cycle}_retained.json",
            "P2@4": cycle_dir / f"p2_at4_cycle{cycle}_retained.json",
            "P2@6": cycle_dir / f"p2_at6_cycle{cycle}_retained.json",
            "P3": cycle_dir / f"p3_arbitre_cycle{cycle}.jsonl",
            "P4": cycle_dir / f"p4_nucleus_cycle{cycle}.jsonl",
        }
        for method, result_path in result_files.items():
            if not result_path.exists():
                continue
            pipeline = method.split("@")[0]
            calls = [row for row in ledger if row.get("pipeline") == pipeline
                     and row.get("cycle") == cycle_label and row.get("repetition") == cycle]
            if method.startswith("P2@"):
                limit = int(method.split("@")[1])
                calls = [row for row in calls if row.get("response_index", 99) <= limit]
            costs = _sum_ledger_costs(calls)
            metrics = compute_metrics(load_pipeline_results(result_path), incidents, costs,
                                      allow_lexical_fallback=allow_lexical_fallback)
            metrics.update({"pipeline": method, "cycle": cycle_label, "repetition": cycle})
            metrics["M08_implementation_effort"] = compute_implementation_effort(pipeline, CODE_ROOT)
            metrics["M09_correlated_miss_rate"] = _compute_m09(
                cycle_dir, pipeline, cycle, incidents, method, allow_lexical_fallback
            )
            all_metrics.append(metrics)
            metric_index[(cycle_label, cycle, method)] = metrics

    # M10 : différence B-A appariée par répétition et architecture.
    for pipeline in ("P1", "P2@3", "P3", "P4"):
        for cycle in range(cycles):
            a = metric_index.get(("A", cycle, pipeline))
            b = metric_index.get(("B", cycle, pipeline))
            if a and b:
                delta = b["M01_detection_recall"] - a["M01_detection_recall"]
                a["M10_persona_delta_recall"] = None
                b["M10_persona_delta_recall"] = round(delta, 4)

    comparisons = []
    for cycle in range(cycles):
        for method, control in (("P1", "P2@6"), ("P3", "P2@4"), ("P4", "P2@6")):
            left = metric_index.get(("A", cycle, method))
            right = metric_index.get(("A", cycle, control))
            if left and right:
                comparisons.append(_comparison_record(method, control, cycle, left, right, "equal_responses"))
        for method in ("P1", "P3", "P4"):
            left = metric_index.get(("A", cycle, method))
            right = metric_index.get(("A", cycle, "P2@3"))
            if left and right:
                comparisons.append(_comparison_record(method, "P2@3", cycle, left, right, "budget_inegal"))

    cycle_c = _cycle_c_decision(all_metrics)
    
    # Agrégation par pipeline (médiane sur cycles)
    summary = aggregate_metrics(all_metrics)
    
    # Sauvegarde
    report_path = results_dir / "metrics_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "per_cycle": all_metrics,
            "summary": summary,
            "question_0_comparisons": comparisons,
            "ledger_rows": len(ledger),
            "D4_matching_backend": ("all-MiniLM-L6-v2" if not allow_lexical_fallback
                                     else "lexical_jaccard_mock_only"),
            "cycle_c_decision": cycle_c,
            "M09": {
                "per_method": [
                    {"pipeline": m["pipeline"], "cycle": m["cycle"], "repetition": m["repetition"],
                     **m["M09_correlated_miss_rate"]}
                    for m in all_metrics if m.get("M09_correlated_miss_rate")
                ]
            },
        }, f, ensure_ascii=False, indent=2)
    
    # CSV summary
    csv_path = results_dir / "summary.csv"
    write_summary_csv(summary, csv_path)
    
    return all_metrics, report_path


def _sum_ledger_costs(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    def nullable_sum(key: str):
        values = [row.get(key) for row in rows]
        return sum(values) if values and all(value is not None for value in values) else None
    return {
        "llm_responses": len(rows),
        "input_tokens": nullable_sum("input_tokens"),
        "output_tokens": nullable_sum("output_tokens"),
        "wall_time_ms": nullable_sum("wall_time_ms"),
        "estimated_cost_usd": nullable_sum("estimated_cost_usd"),
    }


def _compute_m09(cycle_dir: Path, pipeline: str, cycle: int,
                 incidents: List[Dict[str, Any]], method: str,
                 allow_lexical_fallback: bool) -> Optional[Dict[str, Any]]:
    patterns = {
        "P1": f"p1_p1_instance_*_round1_cycle{cycle}_raw.jsonl",
        "P2": f"p2_instance_*_cycle{cycle}_raw.jsonl",
        "P3": f"p3_p3_parseur_*_cycle{cycle}.jsonl",
        "P4": f"p4_p4_parseur_*_cycle{cycle}.jsonl",
    }
    if pipeline == "P0":
        return None
    files = sorted(cycle_dir.glob(patterns[pipeline]))
    limit = int(method.split("@")[1]) if method.startswith("P2@") else 3
    files = files[:limit]
    if not files:
        return None
    outputs = [load_pipeline_results(path, limit=32) for path in files]
    missed = []
    for incident in incidents:
        if not any(match_assertion_to_incident(
            assertion, [incident], allow_lexical_fallback=allow_lexical_fallback
        ) for output in outputs for assertion in output):
            missed.append(incident.get("incident_id"))
    by_type = {}
    incident_types = sorted({incident.get("type", "UNKNOWN") for incident in incidents})
    for incident_type in incident_types:
        population = [incident for incident in incidents if incident.get("type", "UNKNOWN") == incident_type]
        missed_type = [incident for incident in population if incident.get("incident_id") in missed]
        by_type[incident_type] = {
            "rate": round(len(missed_type) / len(population), 4) if population else None,
            "missed": [incident.get("incident_id") for incident in missed_type],
            "total": len(population),
        }
    return {
        "rate": round(len(missed) / len(incidents), 4) if incidents else None,
        "missed": missed,
        "readers": len(files),
        "by_incident_type": by_type,
    }


def _comparison_record(method: str, control: str, repetition: int,
                       left: Dict[str, Any], right: Dict[str, Any], budget_relation: str) -> Dict[str, Any]:
    left_cost = left["M05_cost_per_detection"]
    right_cost = right["M05_cost_per_detection"]
    return {
        "method": method,
        "control": control,
        "cycle": "A",
        "repetition": repetition,
        "llm_responses": {"method": left["M08_implementation_effort"]["llm_calls_per_cycle"],
                          "control": int(control.split("@")[1])},
        "input_tokens": {"method_per_tp": left_cost["input_tokens_per_tp"], "control_per_tp": right_cost["input_tokens_per_tp"]},
        "output_tokens": {"method_per_tp": left_cost["output_tokens_per_tp"], "control_per_tp": right_cost["output_tokens_per_tp"]},
        "wall_time_ms": {"method_per_tp": left_cost["wall_time_ms_per_tp"], "control_per_tp": right_cost["wall_time_ms_per_tp"]},
        "estimated_cost_usd": {"method_per_tp": left_cost["estimated_cost_usd_per_tp"], "control_per_tp": right_cost["estimated_cost_usd_per_tp"]},
        "budget_relation": budget_relation,
        "metrics": {key: {"method": left.get(key), "control": right.get(key)} for key in
                    ("M01_detection_recall", "M02_localization_precision", "M03_false_signal_rate",
                     "M07_closure_appropriate", "M09_correlated_miss_rate", "M10_persona_delta_recall")},
    }


def _cycle_c_decision(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Applique la porte préenregistrée §1quater sur M09 à N=3."""
    native = {"P1", "P2@3", "P3", "P4"}
    rates = {label: [m["M09_correlated_miss_rate"]["rate"] for m in metrics
                     if m["cycle"] == label and m["pipeline"] in native
                     and m.get("M09_correlated_miss_rate", {}).get("rate") is not None]
             for label in ("A", "B")}
    aggregates = {label: (sum(values) / len(values) if values else None) for label, values in rates.items()}
    if aggregates["A"] is None or aggregates["B"] is None:
        return {"triggered": None, "reason": "cycles_A_B_incomplets", "M09_aggregate": aggregates}
    relative_drop = ((aggregates["A"] - aggregates["B"]) / aggregates["A"]
                     if aggregates["A"] > 0 else None)
    triggered = (relative_drop is None or relative_drop < 1 / 3) or aggregates["B"] >= 0.25
    return {
        "triggered": triggered,
        "M09_aggregate": aggregates,
        "relative_drop_A_to_B": relative_drop,
        "rule": "trigger if relative drop < 1/3 OR Cycle B M09 >= 0.25",
    }


def aggregate_metrics(per_cycle: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Médiane + IQR par pipeline sur métriques clés."""
    from statistics import median

    def percentile(values, fraction):
        ordered = sorted(values)
        if not ordered:
            return 0.0
        position = (len(ordered) - 1) * fraction
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        weight = position - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight
    
    by_pipeline = defaultdict(list)
    for m in per_cycle:
        by_pipeline[(m["pipeline"], m["cycle"])].append(m)
    
    summary = {}
    for (pipeline, cycle_label), cycles in by_pipeline.items():
        def med(key):
            vals = [c[key] for c in cycles if c[key] is not None]
            return float(median(vals)) if vals else 0.0
        
        def iqr(key):
            vals = [c[key] for c in cycles if c[key] is not None]
            if len(vals) < 2:
                return 0.0
            q75, q25 = percentile(vals, 0.75), percentile(vals, 0.25)
            return float(q75 - q25)
        
        summary[f"{pipeline}-{cycle_label}"] = {
            "pipeline": pipeline,
            "cycle": cycle_label,
            "M01_recall_median": med("M01_detection_recall"),
            "M01_recall_iqr": iqr("M01_detection_recall"),
            "M02_precision_median": med("M02_localization_precision"),
            "M02_precision_iqr": iqr("M02_localization_precision"),
            "M03_false_signal_median": med("M03_false_signal_rate"),
            "M03_false_signal_iqr": iqr("M03_false_signal_rate"),
            "M05_cost_vector": {
                key: [c["M05_cost_per_detection"].get(key) for c in cycles]
                for key in ("llm_responses_per_tp", "input_tokens_per_tp", "output_tokens_per_tp",
                            "wall_time_ms_per_tp", "estimated_cost_usd_per_tp")
            },
            "M08_loc": cycles[0].get("M08_implementation_effort", {}).get("lines_of_code", 0),
            "M08_llm_calls": cycles[0].get("M08_implementation_effort", {}).get("llm_calls_per_cycle", 0),
            "cycles": len(cycles)
        }
    
    return summary


def write_summary_csv(summary: Dict, path: Path) -> None:
    """Écrit summary.csv lisible par instance analyse sans code."""
    fieldnames = [
        "pipeline", "cycle", "M01_recall_median", "M01_recall_iqr",
        "M02_precision_median", "M02_precision_iqr",
        "M03_false_signal_median", "M03_false_signal_iqr",
        "M05_cost_vector",
        "M08_loc", "M08_llm_calls", "cycles"
    ]
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for vals in summary.values():
            writer.writerow(vals)


# === Test unitaire ===
def test_metrics():
    """Test basique métriques."""
    gt = [
        {"incident_id": "INC-01", "type": "CONTRADICTION_INTRA",
         "description_courte": "Contradiction détectée",
         "source_ref_origine": {"session_id": "s1", "tour_n": 5},
         "source_ref_reprise": {"session_id": "s1", "tour_n": 8}},
        {"incident_id": "INC-02", "type": "DERIVE",
         "description_courte": "Dérive β=N",
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
    
    m = compute_metrics(results, gt, {"llm_responses": 1, "input_tokens": 1000,
                                      "output_tokens": 100, "wall_time_ms": 5000,
                                      "estimated_cost_usd": None})
    
    assert m["M01_detection_recall"] == 1.0
    assert m["M02_localization_precision"] == 1.0
    assert m["M03_false_signal_rate"] == 0.0
    assert m["M04_confidence_calibration"]["FORT"] == 1.0
    
    # Assertions avec faux positif
    results_with_fp = results + [
        {"text": "Hallucination", "source_ref": {"session_id": "s9", "tour_n": 99},
         "epistemic_state": "T", "confidence": "FAIBLE"}
    ]
    
    m2 = compute_metrics(results_with_fp, gt)
    assert m2["M03_false_signal_rate"] == 0.3333
    
    print("[OK] test_metrics passed")


if __name__ == "__main__":
    test_metrics()
