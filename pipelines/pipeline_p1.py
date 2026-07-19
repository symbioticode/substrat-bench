"""
pipelines/pipeline_p1.py — Sprint 1 : Débat multi-instances (P1)
Contact autorisé entre instances — R rounds, révision itérative.
Agrégation finale = même code que P2 (vote majoritaire) pour isoler variable "contact".
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field

from pipelines.common.isolation import (
    isolated_call, IsolationConfig, 
    build_debate_round_messages, validate_isolation
)
from pipelines.common.prompts import get_prompt
from pipelines.common.schemas import SourceRef, StructuredAssertion, DialogueAct, EpistemicState
from pipelines.common.agregation import SemanticClusterer, Assertion, ClusteredAssertion, majority_vote_aggregation


@dataclass
class P1InstanceRound:
    instance_id: str
    round_num: int
    raw_output: str
    assertions: List[StructuredAssertion]


@dataclass
class P1InstanceTrace:
    instance_id: str
    rounds: List[P1InstanceRound]  # Histórico complet par instance


@dataclass
class P1Result:
    traces: List[P1InstanceTrace]
    final_clustered: List[ClusteredAssertion]
    final_retained: List[ClusteredAssertion]


def parse_structured_output(raw_output: str, instance_id: str) -> List[StructuredAssertion]:
    """Parse JSONL → StructuredAssertion (identique P0/P2)."""
    assertions = []
    for line in raw_output.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            src_data = data["source_ref"]
            src = SourceRef(
                session_id=src_data["session_id"],
                tour_n=src_data["tour_n"],
                locuteur=src_data.get("locuteur", "")
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
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[P1 {instance_id} WARNING] Ligne ignorée: {e}")
            continue
    return assertions


def run_p1_debate(
    client: Any,
    model: str,
    corpus_text: str,
    n_instances: int = 3,
    n_rounds: int = 2,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    **kwargs
) -> List[P1InstanceTrace]:
    """
    Exécute débat multi-rounds P1.
    
    Round 1 : instances isolées (identique P2)
    Round 2..R : chaque instance reçoit sa sortie précédente + sorties ANONYMISÉES des autres
    
    Returns: traces complètes par instance (tous rounds conservés §2 Sprint 2)
    """
    config = IsolationConfig(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    # Stockage sorties par round pour injection round suivant
    all_outputs_by_round = {}  # round_num -> {instance_id: raw_output}
    traces = []
    
    for inst_idx in range(n_instances):
        instance_id = f"p1_instance_{inst_idx}"
        instance_seed = seed * 1000 + inst_idx
        instance_rounds = []
        
        own_previous = None
        
        for round_num in range(1, n_rounds + 1):
            if round_num == 1:
                # Round 1 : isolation stricte
                prompt = get_prompt("P1_round1", corpus_text=corpus_text)
                messages = build_debate_round_messages(
                    prompt_fixe=prompt,  # Le prompt contient déjà le corpus
                    corpus_text="",       # Déjà dans prompt
                    own_previous_output="",
                    other_outputs_anonymized=[],
                    round_num=1
                )
                # Validation isolation
                validate_isolation(messages)
            else:
                # Round N>1 : injection sorties autres instances
                other_outputs = [
                    all_outputs_by_round[round_num - 1][other_id]
                    for other_id in all_outputs_by_round[round_num - 1]
                    if other_id != instance_id
                ]
                
                prompt = get_prompt("P1_roundN", 
                    corpus_text=corpus_text,
                    own_previous_output=own_previous,
                    other_outputs=other_outputs
                )
                messages = build_debate_round_messages(
                    prompt_fixe=prompt,
                    corpus_text="",
                    own_previous_output=own_previous,
                    other_outputs_anonymized=other_outputs,
                    round_num=round_num
                )
                # Validation : DOIT contenir sorties autres instances
                content = messages[0]["content"]
                assert "SORTIES AUTRES INSTANCES" in content, "INJECTION CONTEXTE ÉCHOUÉE"
                for other_out in other_outputs:
                    assert other_out[:50] in content, f"Sortie autre instance manquante dans round {round_num}"
            
            # Appel LLM isolé
            raw_output = isolated_call(client, config, messages[0]["content"], "")
            
            # Sauvegarde pour round suivant
            if round_num not in all_outputs_by_round:
                all_outputs_by_round[round_num] = {}
            all_outputs_by_round[round_num][instance_id] = raw_output
            
            # Parse
            assertions = parse_structured_output(raw_output, instance_id)
            own_previous = raw_output
            
            instance_rounds.append(P1InstanceRound(
                instance_id=instance_id,
                round_num=round_num,
                raw_output=raw_output,
                assertions=assertions
            ))
            
            print(f"[P1] {instance_id} Round {round_num}: {len(assertions)} assertions")
        
        traces.append(P1InstanceTrace(instance_id=instance_id, rounds=instance_rounds))
    
    return traces


def aggregate_p1_final(
    traces: List[P1InstanceTrace],
    similarity_threshold: float = 0.50,
    vote_threshold: float = 2/3
) -> P1Result:
    """
    Agrégation FINALE (round R) par vote majoritaire — MÊME CODE que P2.
    Seule variable = contact inter-instances pendant rounds.
    """
    # Prendre seulement round final
    final_assertions = []
    for trace in traces:
        final_round = trace.rounds[-1]
        for a in final_round.assertions:
            final_assertions.append(Assertion(
                instance_id=trace.instance_id,
                text=a.text,
                source_ref={"session_id": a.source_ref.session_id, "tour_n": a.source_ref.tour_n},
                confidence=None,
                reasoning=None
            ))
    
    # Clustering + vote majoritaire (identique P2)
    clusterer = SemanticClusterer(similarity_threshold=similarity_threshold)
    clustered = clusterer.cluster(final_assertions)
    
    n_instances = len(traces)
    min_votes = int(n_instances * vote_threshold)
    retained = [c for c in clustered if c.instance_count >= min_votes]
    
    return P1Result(
        traces=traces,
        final_clustered=clustered,
        final_retained=retained
    )


def save_p1_result(result: P1Result, output_dir: Path, cycle: int) -> None:
    """Sauvegarde traces complètes (tous rounds) + agrégats finaux."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Traces complètes par instance (tous rounds)
    for trace in result.traces:
        for round_data in trace.rounds:
            path = output_dir / f"p1_{trace.instance_id}_round{round_data.round_num}_cycle{cycle}_raw.jsonl"
            path.write_text(round_data.raw_output, encoding='utf-8')
    
    # Clusterisés finaux
    with open(output_dir / f"p1_cycle{cycle}_clustered.json", 'w') as f:
        json.dump([c.to_dict() for c in result.final_clustered], f, ensure_ascii=False, indent=2)
    
    # Retenus
    with open(output_dir / f"p1_cycle{cycle}_retained.json", 'w') as f:
        json.dump([c.to_dict() for c in result.final_retained], f, ensure_ascii=False, indent=2)


def run_p1_cycle(
    client: Any,
    model: str,
    corpus_path: Path,
    output_base: Path,
    cycle_num: int,
    n_instances: int = 3,
    n_rounds: int = 2,
    seed: int = 42,
    similarity_threshold: float = 0.50,
    vote_threshold: float = 2/3,
    **kwargs
) -> Dict[str, Any]:
    """Interface pour run_experiment.py."""
    corpus_text = corpus_path.read_text(encoding='utf-8')
    output_dir = output_base / f"cycle_{cycle_num}" / "raw_outputs"
    
    print(f"[P1 Cycle {cycle_num}] Débat {n_instances} instances × {n_rounds} rounds...")
    
    traces = run_p1_debate(
        client, model, corpus_text,
        n_instances=n_instances, n_rounds=n_rounds, seed=seed + cycle_num * 1000,
        max_tokens=kwargs.get('max_tokens', 2000),
        temperature=kwargs.get('temperature', 0.6)
    )
    
    result = aggregate_p1_final(traces, similarity_threshold, vote_threshold)
    save_p1_result(result, output_dir, cycle_num)
    
    return {
        "pipeline": "P1",
        "cycle": cycle_num,
        "n_instances": n_instances,
        "n_rounds": n_rounds,
        "assertions_final": len(result.final_retained),
        "clusters_total": len(result.final_clustered),
        "output_path": str(output_dir / f"p1_cycle{cycle_num}_retained.json"),
        "assertions": [c.to_dict() for c in result.final_retained]
    }


if __name__ == "__main__":
    # Test isolation + injection contexte
    from pipelines.common.isolation import test_isolation_assertion, test_debate_context_injection
    test_isolation_assertion()
    test_debate_context_injection()
    print("\n✅ P1 unit tests passed")