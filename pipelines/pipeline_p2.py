"""
pipelines/pipeline_p2.py — Sprint 1 : Vote majoritaire isolé (P2)
6 instances isolées ; vues imbriquées P2@3, P2@4 et P2@6.
Baseline qui doit être prise au sérieux (Huang et al.)
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from pipelines.common.isolation import isolated_call, IsolationConfig, CallMetadata
from pipelines.common.prompts import get_prompt, get_prompt_with_persona
from pipelines.common.schemas import SourceRef, StructuredAssertion, DialogueAct, EpistemicState, iter_json_objects
from pipelines.common.agregation import Assertion, ClusteredAssertion, SemanticClusterer


def run_p2_instances(
    client: Any,
    model: str,
    corpus_text: str,
    n_instances: int = 6,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    cycle_label: str = "A",
    cycle_num: int = 0,
    provider: str = "unknown",
    ledger=None,
) -> Tuple[List[List[StructuredAssertion]], List[str]]:
    """N instances isolées — même prompt, contextes vierges."""
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature, provider=provider)
    
    all_assertions = []
    raw_outputs = []
    
    for i in range(n_instances):
        instance_seed = seed * 1000 + i
        instance_id = f"p2_instance_{i}"
        
        # Prompt avec injection persona si Cycle B
        if cycle_label == "B":
            # Les trois postures sont répétées V/T/C/V/T/C.
            prompt = get_prompt_with_persona("P2_extraction", instance_id=f"p2_instance_{i % 3}", corpus_text=corpus_text)
        else:
            prompt = get_prompt("P2_extraction", corpus_text=corpus_text)
        
        raw = isolated_call(
            client, config, prompt, "",
            metadata=CallMetadata("P2", cycle_label, cycle_num, "independent_reader", 1,
                                  i + 1, instance_seed),
            ledger=ledger,
        )
        raw_outputs.append(raw)
        
        # Parse
        assertions = []
        for data in iter_json_objects(raw, limit=32):
            try:
                src = SourceRef(
                    session_id=data["source_ref"]["session_id"],
                    tour_n=data["source_ref"]["tour_n"],
                    locuteur=data["source_ref"].get("locuteur", "")
                )
                assertion = StructuredAssertion(
                    text=data["text"],
                    dialogue_act=DialogueAct(data["dialogue_act"]),
                    epistemic_state=EpistemicState(data["epistemic_state"]),
                    source_ref=src,
                    parseur_id=instance_id,
                    reasoning=data.get("reasoning")
                )
                assertions.append(assertion)
            except (KeyError, ValueError):
                continue
        
        all_assertions.append(assertions)
        print(f"[P2] Instance {i}: {len(assertions)} assertions")
    
    return all_assertions, raw_outputs


def aggregate_p2_vote(
    all_assertions: List[List[StructuredAssertion]],
    required_votes: int,
    similarity_threshold: float = 0.36,
) -> List[ClusteredAssertion]:
    """Agrégation vote majoritaire (identique code P1 final)."""
    # Aplatir avec instance_id
    flat = []
    for inst_idx, assertions in enumerate(all_assertions):
        for a in assertions:
            flat.append(Assertion(
                instance_id=f"p2_instance_{inst_idx}",
                text=a.text,
                source_ref={"session_id": a.source_ref.session_id, "tour_n": a.source_ref.tour_n},
                epistemic_state=a.epistemic_state.value,
                confidence=None,
                reasoning=None
            ))
    
    # Clustering + vote majoritaire
    clusterer = SemanticClusterer(similarity_threshold=similarity_threshold)
    clustered = clusterer.cluster(flat)
    # Majorité stricte : 2/3, 3/4, 4/6. Une égalité 2/4 ou 3/6 est rejetée.
    return [c for c in clustered if c.instance_count >= required_votes]


def run_p2(
    client: Any,
    model: str,
    corpus_text: str,
    output_dir: Path,
    n_instances: int = 6,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    similarity_threshold: float = 0.36,
    vote_threshold: float = 2/3,
    cycle_num: int = 0,
    cycle_label: str = "A",
    **kwargs
) -> Dict[str, List[ClusteredAssertion]]:
    """Pipeline P2 complet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Instances isolées
    if n_instances != 6:
        raise ValueError("v0.3.0 exige exactement six lectures P2 imbriquées")
    all_assertions, raw_outputs = run_p2_instances(
        client, model, corpus_text,
        n_instances=n_instances, seed=seed,
        max_tokens=max_tokens, temperature=temperature,
        cycle_label=cycle_label, cycle_num=cycle_num,
        provider=kwargs.get("provider", "unknown"), ledger=kwargs.get("ledger"),
    )
    
    # Sauvegarde brute par instance
    for i, raw in enumerate(raw_outputs):
        raw_path = output_dir / f"p2_instance_{i}_cycle{cycle_num}_raw.jsonl"
        raw_path.write_text(raw, encoding="utf-8")
    
    # Agrégation
    views = {}
    for size, required in ((3, 2), (4, 3), (6, 4)):
        label = f"P2@{size}"
        views[label] = aggregate_p2_vote(
            all_assertions[:size], similarity_threshold=similarity_threshold,
            required_votes=required,
        )
        agg_path = output_dir / f"p2_at{size}_cycle{cycle_num}_retained.json"
        agg_path.write_text(json.dumps([c.to_dict() for c in views[label]], ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "raw_outputs": [f"p2_instance_{i}_cycle{cycle_num}_raw.jsonl" for i in range(6)],
        "prefixes": {"P2@3": [0, 1, 2], "P2@4": [0, 1, 2, 3], "P2@6": [0, 1, 2, 3, 4, 5]},
        "required_votes": {"P2@3": 2, "P2@4": 3, "P2@6": 4},
    }
    (output_dir / f"p2_cycle{cycle_num}_prefix_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[P2 Cycle {cycle_num} ({cycle_label})] " + ", ".join(f"{k}={len(v)}" for k, v in views.items()))
    return views


def run_p2_cycle(
    client: Any,
    model: str,
    corpus_path: Path,
    output_base: Path,
    cycle_num: int,
    n_instances: int = 6,
    seed: int = 42,
    similarity_threshold: float = 0.36,
    vote_threshold: float = 2/3,
    cycle_label: str = "A",
    **kwargs
) -> Dict[str, Any]:
    """Interface pour run_experiment.py."""
    corpus_text = corpus_path.read_text(encoding='utf-8')
    output_dir = output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"
    
    views = run_p2(
        client, model, corpus_text, output_dir,
        n_instances=n_instances, seed=seed + cycle_num * 1000,
        cycle_num=cycle_num, cycle_label=cycle_label,
        similarity_threshold=similarity_threshold,
        vote_threshold=vote_threshold, **kwargs
    )
    
    return {
        "pipeline": "P2",
        "cycle": cycle_num,
        "cycle_label": cycle_label,
        "n_instances": n_instances,
        "assertions_final": len(views["P2@3"]),
        "views": {key: [c.to_dict() for c in value] for key, value in views.items()},
        "output_path": str(output_dir / f"p2_at3_cycle{cycle_num}_retained.json"),
        "assertions": [c.to_dict() for c in views["P2@3"]]
    }


if __name__ == "__main__":
    # Test vote majoritaire
    from pipelines.common.agregation import test_majority_vote
    test_majority_vote()
    print("\n✅ P2 aggregation test passed")
