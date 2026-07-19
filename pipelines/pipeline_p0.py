"""
pipelines/pipeline_p0.py — Sprint 1 : Passe unique (P0)
Plancher de référence — 1 instance, 1 appel, sortie structurée avec source_ref
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from pipelines.common.isolation import isolated_call, IsolationConfig, validate_isolation
from pipelines.common.prompts import get_prompt
from pipelines.common.schemas import (
    SourceRef, StructuredAssertion, DialogueAct, EpistemicState
)


@dataclass
class P0Output:
    """Sortie complète P0."""
    assertions: List[StructuredAssertion]
    raw_output: str
    tokens_estimate: int
    latency_ms: int
    model: str
    seed: int


def parse_structured_output(raw_output: str, parseur_id: str = "p0") -> List[StructuredAssertion]:
    """Parse JSONL → liste StructuredAssertion avec validation basique."""
    assertions = []
    for line_num, line in enumerate(raw_output.strip().split('\n'), 1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            
            # Validation champs requis
            required = ["text", "dialogue_act", "epistemic_state", "source_ref"]
            missing = [f for f in required if f not in data]
            if missing:
                print(f"[P0 WARNING] Ligne {line_num}: champs manquants {missing}")
                continue
            
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
                parseur_id=parseur_id,
                reasoning=data.get("reasoning")
            )
            assertions.append(assertion)
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"[P0 WARNING] Ligne {line_num} ignorée: {e}")
            continue
    
    return assertions


def run_p0(
    client: Any,
    model: str,
    corpus_text: str,
    output_dir: Path,
    seed: int = 42,
    max_tokens: int = 2000,
    temperature: float = 0.6,
    cycle_num: int = 0
) -> P0Output:
    """
    Exécute pipeline P0 complet.
    
    Args:
        client: Client LLM (doit implémenter create_message)
        model: Nom du modèle (D2 — unique pour tout le banc d'essai)
        corpus_text: Corpus de test complet
        output_dir: Dossier de sortie (results/cycle_<n>/raw_outputs/)
        seed: Seed pour reproductibilité
        max_tokens, temperature: Paramètres génération
        cycle_num: Numéro de cycle (pour nommage fichiers)
    
    Returns:
        P0Output avec assertions parsées
    """
    start_time = time.perf_counter()
    
    config = IsolationConfig(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    # Prompt P0 avec source_ref obligatoire
    prompt = get_prompt("P0_extraction", corpus_text=corpus_text)
    
    # Appel isolé garanti
    raw_output = isolated_call(client, config, prompt, corpus_text)
    
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    tokens_estimate = len(raw_output.split()) * 1.3  # Approximation grossière
    
    # Parse sortie
    assertions = parse_structured_output(raw_output, parseur_id="p0_single")
    
    output = P0Output(
        assertions=assertions,
        raw_output=raw_output,
        tokens_estimate=int(tokens_estimate),
        latency_ms=latency_ms,
        model=model,
        seed=seed
    )
    
    # Sauvegarde brute + parsée
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Brut (pour audit)
    raw_path = output_dir / f"p0_cycle{cycle_num}_raw.jsonl"
    raw_path.write_text(raw_output, encoding='utf-8')
    
    # Parsée (pour métriques)
    parsed_path = output_dir / f"p0_cycle{cycle_num}_parsed.jsonl"
    with open(parsed_path, 'w', encoding='utf-8') as f:
        for a in assertions:
            f.write(json.dumps(a.to_dict(), ensure_ascii=False) + '\n')
    
    print(f"[P0] Cycle {cycle_num}: {len(assertions)} assertions, {latency_ms}ms, ~{int(tokens_estimate)} tokens")
    
    return output


# === Interface pour run_experiment.py ===
def run_p0_cycle(
    client: Any,
    model: str,
    corpus_path: Path,
    output_base: Path,
    cycle_num: int,
    seed: int = 42,
    **kwargs
) -> Dict[str, Any]:
    """
    Fonction appelée par run_experiment.py pour un cycle P0.
    
    Returns dict avec métriques brutes pour aggregation ultérieure.
    """
    corpus_text = corpus_path.read_text(encoding='utf-8')
    output_dir = output_base / f"cycle_{cycle_num}" / "raw_outputs"
    
    result = run_p0(
        client=client,
        model=model,
        corpus_text=corpus_text,
        output_dir=output_dir,
        seed=seed + cycle_num * 1000,  # Seed dérivé déterministe
        cycle_num=cycle_num,
        **kwargs
    )
    
    return {
        "pipeline": "P0",
        "cycle": cycle_num,
        "assertions_count": len(result.assertions),
        "latency_ms": result.latency_ms,
        "tokens_estimate": result.tokens_estimate,
        "output_path": str(output_dir / f"p0_cycle{cycle_num}_parsed.jsonl"),
        "assertions": [a.to_dict() for a in result.assertions]
    }


if __name__ == "__main__":
    # Test unitaire basique (mock client)
    class MockClient:
        def create_message(self, model, messages, max_tokens, temperature, **kwargs):
            class MockResponse:
                content = [type('obj', (object,), {'text': '''{"text": "Budget 10M€", "dialogue_act": "Inform", "epistemic_state": "T", "source_ref": {"session_id": "s1", "tour_n": 1}, "reasoning": "Explicite tour 1"}\n{"text": "Budget 15M€ contradiction", "dialogue_act": "Disagree", "epistemic_state": "B", "source_ref": {"session_id": "s1", "tour_n": 2}, "reasoning": "Contradiction tour 1"}'''})()]
            return MockResponse()
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        corpus = "Session s1, tour 1: Alice dit 'Budget 10M€'. Tour 2: Bob dit 'Budget 15M€'."
        
        result = run_p0(
            client=MockClient(),
            model="test-model",
            corpus_text=corpus,
            output_dir=output_dir,
            cycle_num=0
        )
        
        assert len(result.assertions) == 2
        assert result.assertions[0].source_ref.tour_n == 1
        assert result.assertions[1].epistemic_state == EpistemicState.B
        print("\n✅ P0 unit test passed")