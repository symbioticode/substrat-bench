"""
pipelines/pipeline_p4.py — Sprint 3 : ETAU/SECS Complet (P4)
3 étages : Parseurs isolés → M Cartographes isolés → 1 Noyau cohérence
Confiance 3 niveaux : FORT / PROBABLE / FAIBLE
Traçabilité Option B (niveau fil, round 2) — D3 par défaut
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from pipelines.common.isolation import (
    isolated_call, IsolationConfig, make_arbiter_call, validate_isolation
)
from pipelines.common.prompts import get_prompt
from pipelines.common.schemas import (
    SourceRef, StructuredAssertion, ArbitratedAssertion,
    DialogueAct, EpistemicState, ConfidenceLevel,
    ParseurOutput, validate_output
)
from pipelines.common.agregation import (
    SemanticClusterer, Assertion, ClusteredAssertion, DawidSkeneAggregator
)


@dataclass
class P4Result:
    parseur_outputs: List[ParseurOutput]
    cartographe_outputs: List[Dict[str, Any]]
    nucleus_output: List[ArbitratedAssertion]
    non_convergence_zones: List[Dict[str, Any]]


def parse_parseur_output(raw_output: str, parseur_id: str) -> ParseurOutput:
    """Parse sortie parseur P4 (identique P3)."""
    assertions = []
    for line in raw_output.strip().split('\n'):
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
                parseur_id=parseur_id,
                reasoning=data.get("reasoning")
            )
            assertions.append(assertion)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[P4 Parseur {parseur_id} WARNING] {e}")
    
    return ParseurOutput(parseur_id=parseur_id, assertions=assertions)


def run_p4_parseurs(
    client: Any,
    model: str,
    corpus_text: str,
    n_parseurs: int = 3,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6
) -> List[ParseurOutput]:
    """
    Étage 1 : N parseurs isolés — lisent CHACUN l'intégralité du corpus.
    (Adaptation banc d'essai : partitionnement réel impossible pour convergence measure)
    """
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature)
    prompt = get_prompt("P4_parser", corpus_text=corpus_text)
    
    parseurs = []
    for i in range(n_parseurs):
        parseur_id = f"p4_parseur_{i}"
        raw = isolated_call(client, config, prompt, corpus_text)
        output = parse_parseur_output(raw, parseur_id)
        parseurs.append(output)
        print(f"[P4 Parseurs] {parseur_id}: {len(output.assertions)} assertions")
    
    return parseurs


def run_p4_cartographes(
    client: Any,
    model: str,
    parseur_outputs: List[ParseurOutput],
    n_cartographes: int = 2,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Étage 2 : M cartographes isolés.
    Reçoivent SEULEMENT sorties parseurs — JAMAIS corpus (§2bis).
    Produisent cartes de cohérence (clusters, liens inter-sessions, zones non-convergence).
    """
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature)
    
    # Sérialiser sorties parseurs
    import json
    parser_outputs = []
    for p in parseur_outputs:
        for a in p.assertions:
            d = a.to_dict()
            d["parseur_id"] = p.parseur_id
            parser_outputs.append(d)
    
    cartographes = []
    for i in range(n_cartographes):
        cartographe_id = f"p4_cartographe_{i}"
        
        prompt = get_prompt("P4_cartographe",
            n_parseurs=len(parseur_outputs),
            parser_outputs=json.dumps(parser_outputs, ensure_ascii=False, indent=2),
            total_rounds=2,
            previous_cartographe_output=""
        )
        
        # Appel isolé sans corpus
        raw = make_arbiter_call(client, config, prompt, parser_outputs)
        
        # Parse cartographe output
        try:
            carto_data = json.loads(raw)
        except json.JSONDecodeError:
            # Essayer JSONL
            carto_data = {"clusters": [], "cross_session_links": [], "non_convergence_zones": []}
            for line in raw.strip().split('\n'):
                if line.strip():
                    try:
                        carto_data.update(json.loads(line))
                    except:
                        pass
        
        carto_data["cartographe_id"] = cartographe_id
        cartographes.append(carto_data)
        print(f"[P4 Cartographes] {cartographe_id}: {len(carto_data.get('clusters', []))} clusters")
    
    return cartographes


def run_p4_nucleus(
    client: Any,
    model: str,
    cartographe_outputs: List[Dict[str, Any]],
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6
) -> Dict[str, Any]:
    """
    Étage 3 : Noyau de cohérence unique.
    Reçoit SEULEMENT sorties cartographes — JAMAIS corpus.
    Produit synthèse finale avec confiance 3 niveaux (FORT/PROBABLE/FAIBLE).
    """
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature)
    
    import json
    prompt = get_prompt("P4_nucleus",
        n_cartographes=len(cartographe_outputs),
        cartographe_outputs=json.dumps(cartographe_outputs, ensure_ascii=False, indent=2)
    )
    
    raw = make_arbiter_call(client, config, prompt, cartographe_outputs)
    
    # Parse nucleus output (JSONL assertions + non_convergence)
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
            print(f"[P4 Noyau WARNING] {e}")
    
    return {
        "assertions": assertions,
        "non_convergence_zones": non_convergence
    }


def run_p4(
    client: Any,
    model: str,
    corpus_text: str,
    output_dir: Path,
    n_parseurs: int = 3,
    n_cartographes: int = 2,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    cycle_num: int = 0
) -> P4Result:
    """Pipeline P4 complet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Étage 1 : Parseurs
    parseur_outputs = run_p4_parseurs(
        client, model, corpus_text,
        n_parseurs=n_parseurs, seed=seed,
        max_tokens=max_tokens, temperature=temperature
    )
    
    for p in parseur_outputs:
        (output_dir / f"p4_{p.parseur_id}_cycle{cycle_num}.jsonl").write_text(
            p.to_jsonl(), encoding='utf-8'
        )
    
    # Étage 2 : Cartographes
    cartographe_outputs = run_p4_cartographes(
        client, model, parseur_outputs,
        n_cartographes=n_cartographes, seed=seed,
        max_tokens=max_tokens, temperature=temperature
    )
    
    for c in cartographe_outputs:
        (output_dir / f"p4_{c['cartographe_id']}_cycle{cycle_num}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2), encoding='utf-8'
        )
    
    # Étage 3 : Noyau
    nucleus_result = run_p4_nucleus(
        client, model, cartographe_outputs,
        seed=seed, max_tokens=max_tokens, temperature=temperature
    )
    
    (output_dir / f"p4_nucleus_cycle{cycle_num}.jsonl").write_text(
        "\n".join(json.dumps(a.to_dict(), ensure_ascii=False) for a in nucleus_result["assertions"]),
        encoding='utf-8'
    )
    
    # Non-convergence
    (output_dir / f"p4_non_convergence_cycle{cycle_num}.json").write_text(
        json.dumps(nucleus_result["non_convergence_zones"], ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print(f"[P4 Cycle {cycle_num}] {len(nucleus_result['assertions'])} assertions finales, "
          f"{len(nucleus_result['non_convergence_zones'])} zones non-convergence")
    
    return P4Result(
        parseur_outputs=parseur_outputs,
        cartographe_outputs=cartographe_outputs,
        nucleus_output=nucleus_result["assertions"],
        non_convergence_zones=nucleus_result["non_convergence_zones"]
    )


def run_p4_cycle(
    client: Any,
    model: str,
    corpus_path: Path,
    output_base: Path,
    cycle_num: int,
    n_parseurs: int = 3,
    n_cartographes: int = 2,
    seed: int = 42,
    **kwargs
) -> Dict[str, Any]:
    """Interface pour run_experiment.py."""
    corpus_text = corpus_path.read_text(encoding='utf-8')
    output_dir = output_base / f"cycle_{cycle_num}" / "raw_outputs"
    
    result = run_p4(
        client, model, corpus_text, output_dir,
        n_parseurs=n_parseurs, n_cartographes=n_cartographes,
        seed=seed + cycle_num * 1000, cycle_num=cycle_num, **kwargs
    )
    
    return {
        "pipeline": "P4",
        "cycle": cycle_num,
        "n_parseurs": n_parseurs,
        "n_cartographes": n_cartographes,
        "assertions_final": len(result.nucleus_output),
        "non_convergence_zones": len(result.non_convergence_zones),
        "output_path": str(output_dir / f"p4_nucleus_cycle{cycle_num}.jsonl"),
        "assertions": [a.to_dict() for a in result.nucleus_output],
        "non_convergence": result.non_convergence_zones
    }


if __name__ == "__main__":
    from pipelines.common.schemas import test_schemas, test_validation
    test_schemas()
    test_validation()
    print("\n✅ P4 schema tests passed")