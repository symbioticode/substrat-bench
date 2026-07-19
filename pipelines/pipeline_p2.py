"""
pipelines/pipeline_p2.py — Sprint 1 : Vote majoritaire isolé (P2)
3 instances isolées, même prompt, agrégation vote majoritaire (≥2/3)
Baseline qui doit être prise au sérieux (Huang et al.)
"""

import json
from pathlib import Path
from typing import List, Dict, Any

from pipelines.common.isolation import isolated_call, IsolationConfig, validate_isolation
from pipelines.common.prompts import get_prompt, get_prompt_with_persona
from pipelines.common.schemas import SourceRef, StructuredAssertion, DialogueAct, EpistemicState
from pipelines.common.agregation import (
    Assertion, ClusteredAssertion, SemanticClusterer, majority_vote_aggregation
)


def run_p2_instances(
    client: Any,
    model: str,
    corpus_text: str,
    n_instances: int = 3,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    cycle_label: str = "A",
) -> List[List[StructuredAssertion]]:
    """N instances isolées — même prompt, contextes vierges."""
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature)
    
    all_assertions = []
    
    for i in range(n_instances):
        instance_seed = seed * 1000 + i
        instance_id = f"p2_instance_{i}"
        
        # Prompt avec injection persona si Cycle B
        if cycle_label == "B":
            prompt = get_prompt_with_persona("P2_extraction", instance_id=instance_id, corpus_text=corpus_text)
        else:
            prompt = get_prompt("P2_extraction", corpus_text=corpus_text)
        
        raw = isolated_call(client, config, prompt, corpus_text)
        
        # Parse
        assertions = []
        for line in raw.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
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
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        all_assertions.append(assertions)
        print(f"[P2] Instance {i}: {len(assertions)} assertions")
    
    return all_assertions


def aggregate_p2_vote(
    all_assertions: List[List[StructuredAssertion]],
    similarity_threshold: float = 0.50,
    vote_threshold: float = 2/3
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
                confidence=None,
                reasoning=None
            ))
    
    # Clustering + vote majoritaire
    clusterer = SemanticClusterer(similarity_threshold=similarity_threshold)
    clustered = clusterer.cluster(flat)
    retained = majority_vote_aggregation(clustered, vote_threshold=vote_threshold)
    
    return [c for c in retained if c.retained]


def run_p2(
    client: Any,
    model: str,
    corpus_text: str,
    output_dir: Path,
    n_instances: int = 3,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    similarity_threshold: float = 0.50,
    vote_threshold: float = 2/3,
    cycle_num: int = 0,
    cycle_label: str = "A",
    **kwargs
) -> List[ClusteredAssertion]:
    """Pipeline P2 complet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Instances isolées
    all_assertions = run_p2_instances(
        client, model, corpus_text,
        n_instances=n_instances, seed=seed,
        max_tokens=max_tokens, temperature=temperature,
        cycle_label=cycle_label
    )
    
    # Sauvegarde brute par instance
    for i, assertions in enumerate(all_assertions):
        raw_path = output_dir / f"p2_instance_{i}_cycle{cycle_num}.jsonl"
        with open(raw_path, 'w', encoding='utf-8') as f:
            for a in assertions:
                f.write(json.dumps(a.to_dict(), ensure_ascii=False) + '\n')
    
    # Agrégation
    retained = aggregate_p2_vote(
        all_assertions,
        similarity_threshold=similarity_threshold,
        vote_threshold=vote_threshold
    )
    
    # Sauvegarde agrégée
    agg_path = output_dir / f"p2_cycle{cycle_num}_retained.json"
    with open(agg_path, 'w', encoding='utf-8') as f:
        json.dump([c.to_dict() for c in retained], f, ensure_ascii=False, indent=2)
    
    print(f"[P2 Cycle {cycle_num} ({cycle_label})] {len(retained)} assertions retenues (vote ≥{vote_threshold})")
    
    return retained


def run_p2_cycle(
    client: Any,
    model: str,
    corpus_path: Path,
    output_base: Path,
    cycle_num: int,
    n_instances: int = 3,
    seed: int = 42,
    similarity_threshold: float = 0.50,
    vote_threshold: float = 2/3,
    cycle_label: str = "A",
    **kwargs
) -> Dict[str, Any]:
    """Interface pour run_experiment.py."""
    corpus_text = corpus_path.read_text(encoding='utf-8')
    output_dir = output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"
    
    retained = run_p2(
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
        "assertions_final": len(retained),
        "output_path": str(output_dir / f"p2_cycle{cycle_num}_retained.json"),
        "assertions": [c.to_dict() for c in retained]
    }


if __name__ == "__main__":
    # Test vote majoritaire
    from pipelines.common.agregation import test_majority_vote
    test_majority_vote()
    print("\n✅ P2 aggregation test passed")