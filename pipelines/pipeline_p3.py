"""
pipelines/pipeline_p3.py — Sprint 3 : ETAU/SECS allégé
N parseurs isolés → 1 arbitre unique (confiance binaire FORT/FAIBLE)
Traçabilité niveau fil (Option B par défaut D3)
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from pipelines.common.isolation import isolated_call, IsolationConfig, make_arbiter_call, validate_isolation
from pipelines.common.prompts import get_prompt
from pipelines.common.schemas import (
    SourceRef, StructuredAssertion, ArbitratedAssertion,
    DialogueAct, EpistemicState, ConfidenceLevel, ParseurOutput, ArbitreOutput
)
from pipelines.common.agregation import SemanticClusterer


@dataclass
class P3Result:
    parseur_outputs: List[ParseurOutput]
    arbiter_output: ArbitreOutput
    non_convergence_zones: List[Dict[str, Any]]


def run_p3_parseurs(
    client: Any,
    model: str,
    corpus_text: str,
    n_parseurs: int = 3,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6
) -> List[ParseurOutput]:
    """N parseurs isolés — sortie structurée (PAS de confidence)."""
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature)
    prompt = get_prompt("P3_parseur", corpus_text=corpus_text)
    
    outputs = []
    for i in range(n_parseurs):
        instance_seed = seed * 1000 + i
        
        raw = isolated_call(client, config, prompt, corpus_text)
        
        # Parse JSONL → ParseurOutput
        parseur = ParseurOutput.from_jsonl(raw, parseur_id=f"p3_parseur_{i}")
        outputs.append(parseur)
        print(f"[P3 Parseurs] p3_parseur_{i}: {len(parseur.assertions)} assertions")
    
    return outputs


def run_p3_arbitre(
    client: Any,
    model: str,
    parseur_outputs: List[ParseurOutput],
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6
) -> ArbitreOutput:
    """Arbitre unique — reçoit SEULEMENT sorties parseurs, PAS corpus."""
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature)
    
    # Sérialiser sorties parseurs
    parser_outputs = []
    for p in parseur_outputs:
        for a in p.assertions:
            d = a.to_dict()
            d["parseur_id"] = p.parseur_id
            parser_outputs.append(d)
    
    prompt = get_prompt("P3_arbitre",
        n_parseurs=len(parseur_outputs),
        parser_outputs=json.dumps(parser_outputs, ensure_ascii=False, indent=2)
    )
    
    # Appel arbitre SANS corpus
    raw = make_arbiter_call(client, config, prompt, parser_outputs)
    
    # Parse arbitre output
    assertions = []
    non_convergence = []
    
    for line in raw.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("type") == "non_convergence":
                non_convergence.append(data)
                continue
            
            src = SourceRef(
                session_id=data["source_ref"]["session_id"],
                tour_n=data["source_ref"]["tour_n"],
                locuteur=data["source_ref"].get("locuteur", "")
            )
            
            assertion = ArbitratedAssertion(
                text=data["text"],
                dialogue_act=DialogueAct(data["dialogue_act"]),
                epistemic_state=EpistemicState(data["epistemic_state"]),
                source_ref=src,
                confidence=ConfidenceLevel(data["confidence"]),
                coherence_level=data.get("coherence_level"),
                reasoning=data.get("reasoning")
            )
            assertions.append(assertion)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[P3 Arbiter WARNING] {e}")
    
    return ArbitreOutput(
        assertions=assertions,
        non_convergence_zones=non_convergence
    )


def run_p3(
    client: Any,
    model: str,
    corpus_text: str,
    output_dir: Path,
    n_parseurs: int = 3,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    cycle_num: int = 0
) -> P3Result:
    """Pipeline P3 complet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parseurs
    parseur_outputs = run_p3_parseurs(
        client, model, corpus_text,
        n_parseurs=n_parseurs, seed=seed,
        max_tokens=max_tokens, temperature=temperature
    )
    
    for p in parseur_outputs:
        (output_dir / f"p3_{p.parseur_id}_cycle{cycle_num}.jsonl").write_text(
            p.to_jsonl(), encoding='utf-8'
        )
    
    # Arbitre
    arbiter_output = run_p3_arbitre(
        client, model, parseur_outputs,
        seed=seed, max_tokens=max_tokens, temperature=temperature
    )
    
    (output_dir / f"p3_arbitre_cycle{cycle_num}.jsonl").write_text(
        "\n".join(json.dumps(a.to_dict(), ensure_ascii=False) for a in arbiter_output.assertions),
        encoding='utf-8'
    )
    
    if arbiter_output.non_convergence_zones:
        (output_dir / f"p3_non_convergence_cycle{cycle_num}.json").write_text(
            json.dumps(arbiter_output.non_convergence_zones, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    print(f"[P3 Cycle {cycle_num}] {len(arbiter_output.assertions)} assertions finales "
          f"({sum(1 for a in arbiter_output.assertions if a.confidence == ConfidenceLevel.FORT)} FORT), "
          f"{len(arbiter_output.non_convergence_zones)} zones non-convergence")
    
    return P3Result(
        parseur_outputs=parseur_outputs,
        arbiter_output=arbiter_output,
        non_convergence_zones=arbiter_output.non_convergence_zones
    )


def run_p3_cycle(
    client: Any,
    model: str,
    corpus_path: Path,
    output_base: Path,
    cycle_num: int,
    n_parseurs: int = 3,
    seed: int = 42,
    **kwargs
) -> Dict[str, Any]:
    """Interface pour run_experiment.py."""
    corpus_text = corpus_path.read_text(encoding='utf-8')
    output_dir = output_base / f"cycle_{cycle_num}" / "raw_outputs"
    
    result = run_p3(
        client, model, corpus_text, output_dir,
        n_parseurs=n_parseurs, seed=seed + cycle_num * 1000,
        cycle_num=cycle_num, **kwargs
    )
    
    fort_count = sum(1 for a in result.arbiter_output.assertions if a.confidence == ConfidenceLevel.FORT)
    
    return {
        "pipeline": "P3",
        "cycle": cycle_num,
        "n_parseurs": n_parseurs,
        "assertions_final": len(result.arbiter_output.assertions),
        "fort_count": fort_count,
        "faible_count": len(result.arbiter_output.assertions) - fort_count,
        "non_convergence_zones": len(result.non_convergence_zones),
        "output_path": str(output_dir / f"p3_arbitre_cycle{cycle_num}.jsonl"),
        "assertions": [a.to_dict() for a in result.arbiter_output.assertions],
        "non_convergence": result.non_convergence_zones
    }


if __name__ == "__main__":
    from pipelines.common.schemas import test_schemas, test_validation
    test_schemas()
    test_validation()
    print("\n✅ P3 schema tests passed")