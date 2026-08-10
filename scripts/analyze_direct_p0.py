#!/usr/bin/env python3
"""Analyse descriptive du pilote P0 direct; ne calcule pas M09 normatif."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

TARGETS = {
    "budget_contradiction": ("s1", {"Disagree"}, {"B"}),
    "date_drift": ("s2", {"Project", "Disagree", "FlagGap"}, {"B"}),
    "unsupported_claim": ("s3", {"Project", "FlagGap"}, {"N"}),
    "payment_open_gap": ("s4", {"FlagGap"}, set()),
    "genuine_ambiguity": ("s5", {"FlagAmbiguity"}, set()),
}


def detects(assertions, rule):
    session, acts, states = rule
    return any(
        a.get("source_ref", {}).get("session_id") == session
        and (a.get("dialogue_act") in acts or a.get("epistemic_state") in states)
        for a in assertions
    )


def analyze(manifest):
    by_model = defaultdict(list)
    for run in manifest["runs"]:
        if run.get("status") == "ok":
            by_model[run["model_requested"]].append(run)
    models = {}
    for model, runs in by_model.items():
        models[model] = {
            "runs": len(runs),
            "assertion_counts": [len(r["assertions"]) for r in runs],
            "target_detection_frequency": {
                name: sum(detects(r["assertions"], rule) for r in runs)
                for name, rule in TARGETS.items()
            },
        }
    paired_union = {}
    repeats = manifest["repeats"]
    for name, rule in TARGETS.items():
        paired_union[name] = sum(
            any(detects(r["assertions"], rule) for runs in by_model.values() for r in runs if r["repeat"] == repeat)
            for repeat in range(repeats)
        )
    return {
        "protocol": manifest["protocol"],
        "descriptive_only_not_m09": True,
        "models": models,
        "paired_cross_provider_union_frequency": paired_union,
        "estimated_spend_usd": manifest["estimated_spend_usd"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(json.loads(args.manifest.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
