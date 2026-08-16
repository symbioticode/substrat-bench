"""
pipelines/pipeline_p4.py — Sprint 3 : ETAU/SECS Complet (P4)
3 étages : Parseurs isolés → M Cartographes isolés → 1 Noyau cohérence
Confiance 3 niveaux : FORT / PROBABLE / FAIBLE
Traçabilité Option B (niveau fil, round 2) — D3 par défaut
"""

import json
import secrets
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass

from pipelines.common.isolation import (
    isolated_call, IsolationConfig, make_arbiter_call, CallMetadata
)
from pipelines.common.prompts import get_prompt, get_prompt_with_persona
from pipelines.common.schemas import (
    SourceRef, StructuredAssertion, ArbitratedAssertion,
    DialogueAct, EpistemicState, ConfidenceLevel,
    ParseurOutput, validate_output, iter_json_objects, parse_dialogue_act
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


def parse_cartographer_output(raw: str, cartographer_id: str) -> Dict[str, Any]:
    """Normalise objet enveloppe, tableau ou zones JSONL en une carte commune."""
    objects = list(iter_json_objects(raw, limit=32, flatten_assertions=False))
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError:
        decoded = None
    if isinstance(decoded, dict) and isinstance(decoded.get("clusters"), list):
        result = decoded
    elif isinstance(decoded, list):
        result = {"clusters": [item for item in decoded if isinstance(item, dict)]}
    else:
        result = {"clusters": objects}
    result.setdefault("cross_session_links", [])
    result.setdefault("non_convergence_zones", [])
    result["cartographe_id"] = cartographer_id
    return result


def parse_nucleus_output(raw: str) -> tuple[List[ArbitratedAssertion], List[Dict[str, Any]]]:
    """Parse le niveau fil P4; ancre un tour_range sur son premier tour exact."""
    assertions: List[ArbitratedAssertion] = []
    non_convergence: List[Dict[str, Any]] = []
    for data in iter_json_objects(raw, limit=32):
        try:
            if data.get("type") == "non_convergence":
                non_convergence.append(data)
                continue
            src_data = data["source_ref"]
            tour_n = src_data.get("tour_n")
            if tour_n is None and src_data.get("tour_range"):
                tour_n = src_data["tour_range"][0]
            src = SourceRef(session_id=src_data["session_id"], tour_n=tour_n,
                            locuteur=src_data.get("locuteur", ""))
            assertions.append(ArbitratedAssertion(
                text=data["text"], dialogue_act=parse_dialogue_act(data["dialogue_act"]),
                epistemic_state=EpistemicState(data["epistemic_state"]), source_ref=src,
                confidence=ConfidenceLevel(data["confidence"]),
                coherence_level=data.get("coherence_level"), reasoning=data.get("reasoning")))
        except (KeyError, ValueError, TypeError, IndexError) as exc:
            print(f"[P4 Noyau WARNING] {exc}")
    return assertions, non_convergence


def parse_parseur_output(raw_output: str, parseur_id: str) -> ParseurOutput:
    """Parse sortie parseur P4 (identique P3)."""
    assertions = []
    for data in iter_json_objects(raw_output, limit=32):
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
                parseur_id=parseur_id,
                reasoning=data.get("reasoning")
            )
            assertions.append(assertion)
        except (KeyError, ValueError) as e:
            print(f"[P4 Parseur {parseur_id} WARNING] {e}")
    
    return ParseurOutput(parseur_id=parseur_id, assertions=assertions)


def run_p4_parseurs(
    client: Any,
    model: str,
    corpus_text: str,
    n_parseurs: int = 3,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    cycle_label: str = "A",
    cycle_num: int = 0,
    provider: str = "unknown",
    ledger=None,
) -> List[ParseurOutput]:
    """
    Étage 1 : N parseurs isolés — lisent CHACUN l'intégralité du corpus.
    (Adaptation banc d'essai : partitionnement réel impossible pour convergence measure)
    Injection persona si Cycle B.
    """
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature, provider=provider)
    
    parseurs = []
    for i in range(n_parseurs):
        parseur_id = f"p4_parseur_{i}"
        
        # Prompt avec injection persona si Cycle B
        if cycle_label == "B":
            prompt = get_prompt_with_persona("P4_parser", instance_id=parseur_id, corpus_text=corpus_text)
        else:
            prompt = get_prompt("P4_parser", corpus_text=corpus_text)
        
        raw = isolated_call(
            client, config, prompt, "",
            metadata=CallMetadata("P4", cycle_label, cycle_num, "parser", 1, i + 1, seed * 1000 + i),
            ledger=ledger,
        )
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
    temperature: float = 0.6,
    cycle_label: str = "A",
    cycle_num: int = 0,
    provider: str = "unknown",
    ledger=None,
    reader_order=None,
) -> List[Dict[str, Any]]:
    """
    Étage 2 : M cartographes isolés, entrées anonymisées quant à la persona.
    Reçoivent SEULEMENT sorties parseurs — JAMAIS corpus (§2bis).
    Produisent cartes de cohérence (clusters, liens inter-sessions, zones non-convergence).
    """
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature, provider=provider)
    
    # Sérialiser sorties parseurs
    import json
    ordered = reader_order or list(range(len(parseur_outputs)))
    parser_outputs = [
        {"reader": f"reader_{anonymous_index}",
         "assertions": [{k: v for k, v in a.to_dict().items() if k not in {"parseur_id", "timestamp"}}
                        for a in parseur_outputs[source_index].assertions]}
        for anonymous_index, source_index in enumerate(ordered)
    ]
    
    cartographes = []
    for i in range(n_cartographes):
        cartographe_id = f"p4_cartographe_{i}"
        
        prompt = get_prompt("P4_cartographe",
            n_parseurs=len(parseur_outputs),
            parser_outputs="",
            total_rounds=2,
            previous_cartographe_output=""
        )
        
        # Appel isolé sans corpus
        raw = make_arbiter_call(
            client, config, prompt, parser_outputs,
            metadata=CallMetadata("P4", cycle_label, cycle_num, "cartographer", 2, 4 + i, seed * 1000 + 3 + i),
            ledger=ledger,
        )
        
        carto_data = parse_cartographer_output(raw, cartographe_id)
        cartographes.append(carto_data)
        print(f"[P4 Cartographes] {cartographe_id}: {len(carto_data.get('clusters', []))} clusters")
    
    return cartographes


def run_p4_nucleus(
    client: Any,
    model: str,
    cartographe_outputs: List[Dict[str, Any]],
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    cycle_label: str = "A",
    cycle_num: int = 0,
    provider: str = "unknown",
    ledger=None,
) -> Dict[str, Any]:
    """
    Étage 3 : Noyau de cohérence unique.
    Reçoit SEULEMENT sorties cartographes — JAMAIS corpus.
    Produit synthèse finale avec confiance 3 niveaux (FORT/PROBABLE/FAIBLE).
    """
    config = IsolationConfig(model=model, max_tokens=max_tokens, temperature=temperature, provider=provider)
    
    import json
    prompt = get_prompt("P4_noyau",
        n_cartographes=len(cartographe_outputs),
        cartographe_outputs=""
    )
    
    raw = make_arbiter_call(
        client, config, prompt, cartographe_outputs,
        metadata=CallMetadata("P4", cycle_label, cycle_num, "nucleus", 3, 6, seed * 1000 + 5),
        ledger=ledger,
    )
    
    assertions, non_convergence = parse_nucleus_output(raw)
    
    return {
        "assertions": assertions,
        "non_convergence_zones": non_convergence,
        "raw_output": raw,
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
    cycle_num: int = 0,
    cycle_label: str = "A",
    **kwargs
) -> P4Result:
    """Pipeline P4 complet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Étage 1 : Parseurs
    parseur_outputs = run_p4_parseurs(
        client, model, corpus_text,
        n_parseurs=n_parseurs, seed=seed,
        max_tokens=max_tokens, temperature=temperature,
        cycle_label=cycle_label, cycle_num=cycle_num,
        provider=kwargs.get("provider", "unknown"), ledger=kwargs.get("ledger"),
    )
    
    for p in parseur_outputs:
        (output_dir / f"p4_{p.parseur_id}_cycle{cycle_num}.jsonl").write_text(
            p.to_jsonl(), encoding='utf-8'
        )
    
    # Étage 2 : Cartographes
    reader_order = secrets.SystemRandom().sample(range(len(parseur_outputs)), len(parseur_outputs))
    (output_dir / f"p4_anonymization_cycle{cycle_num}.json").write_text(
        json.dumps({"anonymous_reader_order": [parseur_outputs[i].parseur_id for i in reader_order]}, indent=2),
        encoding="utf-8",
    )
    cartographe_outputs = run_p4_cartographes(
        client, model, parseur_outputs,
        n_cartographes=n_cartographes, seed=seed,
        max_tokens=max_tokens, temperature=temperature,
        cycle_label=cycle_label, cycle_num=cycle_num,
        provider=kwargs.get("provider", "unknown"), ledger=kwargs.get("ledger"),
        reader_order=reader_order,
    )
    
    for c in cartographe_outputs:
        (output_dir / f"p4_{c['cartographe_id']}_cycle{cycle_num}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=2), encoding='utf-8'
        )
    
    # Étage 3 : Noyau
    nucleus_result = run_p4_nucleus(
        client, model, cartographe_outputs,
        seed=seed, max_tokens=max_tokens, temperature=temperature,
        cycle_label=cycle_label, cycle_num=cycle_num,
        provider=kwargs.get("provider", "unknown"), ledger=kwargs.get("ledger"),
    )
    
    (output_dir / f"p4_nucleus_cycle{cycle_num}.jsonl").write_text(
        "\n".join(json.dumps(a.to_dict(), ensure_ascii=False) for a in nucleus_result["assertions"]),
        encoding='utf-8'
    )
    (output_dir / f"p4_nucleus_cycle{cycle_num}_raw.txt").write_text(
        nucleus_result["raw_output"], encoding="utf-8"
    )
    
    # Non-convergence
    (output_dir / f"p4_non_convergence_cycle{cycle_num}.json").write_text(
        json.dumps(nucleus_result["non_convergence_zones"], ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print(f"[P4 Cycle {cycle_num} ({cycle_label})] {len(nucleus_result['assertions'])} assertions finales, "
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
    cycle_label: str = "A",
    **kwargs
) -> Dict[str, Any]:
    """Interface pour run_experiment.py."""
    corpus_text = corpus_path.read_text(encoding='utf-8')
    output_dir = output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"
    
    result = run_p4(
        client, model, corpus_text, output_dir,
        n_parseurs=n_parseurs, n_cartographes=n_cartographes,
        seed=seed + cycle_num * 1000, cycle_num=cycle_num, cycle_label=cycle_label, **kwargs
    )
    
    return {
        "pipeline": "P4",
        "cycle": cycle_num,
        "cycle_label": cycle_label,
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
