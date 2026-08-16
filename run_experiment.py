#!/usr/bin/env python3
"""
run_experiment.py — Orchestrateur banc d'essai ETAU/SECS
Usage: python run_experiment.py --cycles 5 [--pipelines P0,P1,P2,P3,P4]
"""
import argparse
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).parent

# Import pipelines
sys.path.insert(0, str(REPO_ROOT))
from pipelines.pipeline_p0 import run_p0_cycle
from pipelines.pipeline_p1 import run_p1_cycle
from pipelines.pipeline_p2 import run_p2_cycle
from pipelines.pipeline_p3 import run_p3_cycle
from pipelines.pipeline_p4 import run_p4_cycle
from metrics.metrics import run_all_metrics
from pipelines.common.isolation import InferenceLedger
from pipelines.common.agnos_observability import AgnosEventWriter

PIPELINE_FUNCS = {
    "P0": run_p0_cycle,
    "P1": run_p1_cycle,
    "P2": run_p2_cycle,
    "P3": run_p3_cycle,
    "P4": run_p4_cycle,
}

DEFAULT_PIPELINES = ["P0", "P1", "P2", "P3", "P4"]

class MockLLMClient:
    """Client mock pour tests sans clés API."""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {}
        self.call_count = 0
    
    def create_message(self, model: str, messages: List[Dict], max_tokens: int, 
                       temperature: float, **kwargs) -> Any:
        self.call_count += 1
        key = f"call_{self.call_count}"
        content = self.responses.get(key, self._default_response(kwargs.get("seed")))
        
        class MockContent:
            def __init__(self, text): self.text = text
        class MockResponse:
            def __init__(self, text): self.content = [MockContent(text)]
        
        return MockResponse(content)
    
    def _default_response(self, seed=None) -> str:
        # Réponse JSONL générique valide pour test
        return json.dumps({"text": "Assertion test", "dialogue_act": "Inform", "epistemic_state": "T",
                           "source_ref": {"session_id": "s1", "tour_n": 1},
                           "reasoning": f"Mock déterministe seed={seed}"}, ensure_ascii=False)


def load_corpus(corpus_path: Path) -> str:
    """Charge corpus de test (JSON ou texte)."""
    if corpus_path.stat().st_size == 0:
        raise ValueError(f"Corpus vide: {corpus_path}")
    if corpus_path.suffix == ".json":
        with open(corpus_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Format attendu: liste {session_id, tour_n, locuteur, texte}
        if isinstance(data, list):
            lines = []
            for item in data:
                sid = item.get("session_id", "s1")
                tn = item.get("tour_n", 1)
                loc = item.get("locuteur", "Inconnu")
                txt = item.get("texte", "")
                lines.append(f"Session {sid}, tour {tn}: {loc} dit '{txt}'.")
            return "\n".join(lines)
        return json.dumps(data, ensure_ascii=False, indent=2)
    else:
        return corpus_path.read_text(encoding='utf-8')


def get_llm_client(model: str, provider: str = "mock") -> Any:
    """Factory client LLM selon provider."""
    if provider == "mock":
        return MockLLMClient()
    elif provider == "anthropic":
        from anthropic import Anthropic
        sdk = Anthropic()
        class AnthropicAdapter:
            def create_message(self, model, messages, max_tokens, temperature, **kwargs):
                return sdk.messages.create(model=model, messages=messages, max_tokens=max_tokens,
                                           temperature=temperature, **kwargs)
        return AnthropicAdapter()
    elif provider == "openai":
        from openai import OpenAI
        sdk = OpenAI()
        class OpenAIAdapter:
            def create_message(self, model, messages, max_tokens, temperature, **kwargs):
                return sdk.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens,
                                                   temperature=temperature, **kwargs)
        return OpenAIAdapter()
    elif provider == "deepseek":
        from openai import OpenAI
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY absente de l'environnement")
        sdk = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        class DeepSeekAdapter:
            def create_message(self, model, messages, max_tokens, temperature, **kwargs):
                # D2 fige le mode non-thinking pour éviter une variable cachée.
                return sdk.chat.completions.create(
                    model=model, messages=messages, max_tokens=max_tokens,
                    temperature=temperature,
                    extra_body={"thinking": {"type": "disabled"}}, **kwargs)
        return DeepSeekAdapter()
    else:
        raise ValueError(f"Provider inconnu: {provider}")


def run_cycle(
    cycle_num: int,
    pipelines: List[str],
    client: Any,
    model: str,
    corpus_text: str,
    output_base: Path,
    seed: int = 42,
    cycle_label: str = "A",
    agnos_writer: AgnosEventWriter = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """Exécute un cycle complet sur tous les pipelines demandés."""
    print(f"\n{'='*60}")
    print(f"CYCLE {cycle_num + 1} / {kwargs.get('total_cycles', '?')}")
    print(f"{'='*60}")
    
    cycle_results = []
    corpus_path = output_base / f"cycle_{cycle_label}_{cycle_num}" / "corpus_test.json"
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(corpus_text, encoding='utf-8')
    
    for pipeline_name in pipelines:
        if pipeline_name not in PIPELINE_FUNCS:
            print(f"[WARN] Pipeline inconnu: {pipeline_name}")
            continue
        
        func = PIPELINE_FUNCS[pipeline_name]
        agent_id = f"substrat-{pipeline_name.lower()}"
        task = f"cycle_{cycle_label}/repetition_{cycle_num}"
        artifact_ref = f"cycle_{cycle_label}_{cycle_num}/cycle_summary.json"
        if agnos_writer:
            agnos_writer.emit(
                agent_id=agent_id, status="en_cours", task=task,
                detail=f"Démarrage du pipeline {pipeline_name}.",
                lifecycle="actif", health="operationnel",
                pipeline=pipeline_name, cycle=cycle_label,
                repetition=cycle_num, artifact_ref=artifact_ref,
            )
        try:
            print(f"\n--- {pipeline_name} ---")
            pipeline_kwargs = dict(kwargs)
            if pipeline_name == "P2":
                pipeline_kwargs["n_instances"] = 6
            elif pipeline_name == "P1":
                pipeline_kwargs["n_instances"] = 3
            result = func(
                client=client,
                model=model,
                corpus_path=corpus_path,
                output_base=output_base,
                cycle_num=cycle_num,
                seed=seed + cycle_num * 1000,
                cycle_label=cycle_label,
                **pipeline_kwargs
            )
            result["timestamp"] = datetime.now(timezone.utc).isoformat()
            cycle_results.append(result)
            if agnos_writer:
                agnos_writer.emit(
                    agent_id=agent_id, status="succès", task=task,
                    detail=f"Pipeline {pipeline_name} terminé sans exception.",
                    lifecycle="termine", health="operationnel",
                    pipeline=pipeline_name, cycle=cycle_label,
                    repetition=cycle_num, artifact_ref=artifact_ref,
                )
            
        except Exception as e:
            print(f"[ERROR] {pipeline_name} cycle {cycle_num}: {e}")
            import traceback
            traceback.print_exc()
            cycle_results.append({
                "pipeline": pipeline_name,
                "cycle": cycle_num,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            if agnos_writer:
                agnos_writer.emit(
                    agent_id=agent_id, status="échec", task=task,
                    detail=f"Pipeline {pipeline_name} interrompu: {type(e).__name__}: {e}",
                    lifecycle="termine", health="erreur",
                    pipeline=pipeline_name, cycle=cycle_label,
                    repetition=cycle_num, artifact_ref=artifact_ref,
                )
    
    return cycle_results


def update_hypotheses_log(results: List[Dict], hypotheses_path: Path):
    """Met à jour HYPOTHESES.md avec derniers résultats."""
    # Lecture existante
    content = hypotheses_path.read_text(encoding='utf-8') if hypotheses_path.exists() else ""
    
    # Génère nouvelles lignes tableau
    new_rows = []
    for r in results:
        if "error" in r:
            continue
        pipeline = r.get("pipeline", "?")
        cycle = r.get("cycle", 0)
        # Métriques brutes (seront agrégées plus tard)
        new_rows.append(f"| {cycle} | {pipeline} | — | — | — | — | — | — | — | ⏳ Exécuté |")
    
    if new_rows:
        # Insert après ligne "### Cycle X"
        lines = content.split('\n')
        insert_idx = len(lines)
        for i, line in enumerate(lines):
            if line.startswith("### Cycle") or line.startswith("## Synthèse"):
                insert_idx = i
                break
        
        # Trouve fin tableau courant
        for i in range(insert_idx, len(lines)):
            if lines[i].startswith("---") or lines[i].startswith("## "):
                insert_idx = i
                break
        
        # Insère
        lines[insert_idx:insert_idx] = new_rows + [""]
        hypotheses_path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description="Banc d'essai ETAU/SECS")
    parser.add_argument("--cycles", type=int, default=5, help="Nombre de cycles (défaut: 5)")
    parser.add_argument("--pipelines", type=str, default=",".join(DEFAULT_PIPELINES),
                        help=f"Pipelines à exécuter (défaut: tous)")
    parser.add_argument("--model", type=str, default="deepseek-v4-flash",
                        help="Modèle unique (D2)")
    parser.add_argument("--provider", type=str, default="mock",
                        choices=["mock", "anthropic", "openai", "deepseek"],
                        help="Provider LLM (défaut: mock pour test)")
    parser.add_argument("--corpus", type=str, default="corpus/source/corpus_test.json",
                        help="Chemin corpus test")
    parser.add_argument("--output", type=str, default="results",
                        help="Dossier sortie")
    parser.add_argument("--seed", type=int, default=42, help="Seed global")
    parser.add_argument("--max-tokens", type=int, default=4000,
                        help="Plafond uniforme de sortie par appel (D2, défaut: 4000)")
    parser.add_argument("--skip-metrics", action="store_true", help="Ne pas calculer métriques")
    parser.add_argument("--personas", choices=["off", "on", "both"], default="both",
                        help="Cycles A, B ou les deux")
    parser.add_argument("--run-id", default=None,
                        help="Identifiant du run dans les événements AGNOS")
    parser.add_argument("--agnos-events", default=None,
                        help="Flux AGNOS v2 (défaut: <output>/agnos_events.jsonl)")
    
    args = parser.parse_args()
    
    pipelines = [p.strip().upper() for p in args.pipelines.split(",")]
    output_base = REPO_ROOT / args.output
    output_base.mkdir(parents=True, exist_ok=True)
    ledger_path = output_base / "inference_ledger.jsonl"
    if ledger_path.exists():
        print(f"[ERROR] Registre déjà présent: {ledger_path}; utilisez un dossier --output neuf")
        sys.exit(2)
    ledger = InferenceLedger(ledger_path)
    run_id = args.run_id or f"substrat-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    agnos_path = Path(args.agnos_events) if args.agnos_events else output_base / "agnos_events.jsonl"
    if agnos_path.exists():
        print(f"[ERROR] Flux AGNOS déjà présent: {agnos_path}; utilisez une cible neuve")
        sys.exit(2)
    agnos_writer = AgnosEventWriter(agnos_path, run_id)
    
    # Chargement corpus
    corpus_path = REPO_ROOT / args.corpus
    if not corpus_path.exists():
        print(f"[ERROR] Corpus introuvable: {corpus_path}")
        print("Exécutez d'abord: python corpus/generate_corpus.py")
        sys.exit(1)
    
    try:
        corpus_text = load_corpus(corpus_path)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"[ERROR] Corpus invalide: {exc}")
        sys.exit(1)
    print(f"[INFO] Corpus chargé: {len(corpus_text)} chars")
    
    # Client LLM
    client = get_llm_client(args.model, args.provider)
    print(f"[INFO] Client LLM: {args.provider} / {args.model}")
    agnos_writer.emit(
        agent_id="substrat-runner", status="en_cours", task="run expérimental",
        detail="Initialisation du harnais substrat-bench.",
        lifecycle="actif", health="operationnel", artifact_ref=".",
    )
    
    # Paramètres partagés (VARIABLES.md)
    common_kwargs = {
        "max_tokens": args.max_tokens,
        "temperature": 0.6,
        "n_rounds": 2,
        "n_cartographes": 2,
        "similarity_threshold": 0.36,
        "vote_threshold": 2/3,
        "total_cycles": args.cycles,
        "provider": args.provider,
        "ledger": ledger,
    }
    
    all_results = []
    
    # Exécution cycles
    cycle_labels = {"off": ["A"], "on": ["B"], "both": ["A", "B"]}[args.personas]
    for cycle_label in cycle_labels:
      for cycle in range(args.cycles):
        cycle_results = run_cycle(
            cycle_num=cycle,
            pipelines=pipelines,
            client=client,
            model=args.model,
            corpus_text=corpus_text,
            output_base=output_base,
            seed=args.seed,
            cycle_label=cycle_label,
            agnos_writer=agnos_writer,
            **common_kwargs
        )
        all_results.extend(cycle_results)
        
        # Log intermédiaire
        log_path = output_base / f"cycle_{cycle_label}_{cycle}" / "cycle_summary.json"
        log_path.write_text(json.dumps(cycle_results, ensure_ascii=False, indent=2), encoding='utf-8')
    
    # Métriques finales
    if not args.skip_metrics:
        print(f"\n{'='*60}")
        print("CALCUL MÉTRIQUES (M01-M08)")
        print(f"{'='*60}")
        
        gt_path = REPO_ROOT / "corpus/ground_truth/ground_truth.json"
        if gt_path.exists() and gt_path.stat().st_size:
            run_all_metrics(output_base, gt_path, args.cycles, tuple(cycle_labels))
            print(f"[OK] Métriques → {output_base}/metrics_report.json + summary.csv")
        else:
            print(f"[WARN] Ground truth absente ou vide: {gt_path} — métriques non calculées")
    
    # Le mode mock est un gate technique et ne constitue pas une observation
    # expérimentale à verser dans HYPOTHESES.md.
    hypotheses_path = REPO_ROOT / "HYPOTHESES.md"
    if args.provider != "mock":
        update_hypotheses_log(all_results, hypotheses_path)

    errors = [result for result in all_results if "error" in result]
    if set(pipelines) == set(DEFAULT_PIPELINES) and not errors:
        ledger_rows = sum(1 for _ in ledger_path.open(encoding="utf-8"))
        expected = 23 * args.cycles * len(cycle_labels)
        if ledger_rows != expected:
            print(f"[ERROR] Registre incomplet: {ledger_rows} lignes, {expected} attendues")
            agnos_writer.emit(
                agent_id="substrat-runner", status="échec", task="run expérimental",
                detail=f"Registre incomplet: {ledger_rows}/{expected} réponses.",
                lifecycle="termine", health="erreur", artifact_ref="inference_ledger.jsonl",
            )
            sys.exit(3)
    
    # Résumé final
    print(f"\n{'='*60}")
    print("RÉSUMÉ")
    print(f"{'='*60}")
    for r in all_results:
        if "error" not in r:
            print(f"  {r['pipeline']} cycle {r['cycle']}: {r.get('assertions_final', r.get('assertions_count', '?'))} assertions")
        else:
            print(f"  {r['pipeline']} cycle {r['cycle']}: ERROR - {r['error']}")
    
    print(f"\nRésultats dans: {output_base}")
    print(f"Hypothèses log: {hypotheses_path}")
    if errors:
        agnos_writer.emit(
            agent_id="substrat-runner", status="échec", task="run expérimental",
            detail=f"Run terminé avec {len(errors)} erreur(s) de pipeline.",
            lifecycle="termine", health="erreur", artifact_ref=".",
        )
        sys.exit(4)
    agnos_writer.emit(
        agent_id="substrat-runner", status="succès", task="run expérimental",
        detail=f"Run terminé: {len(all_results)} exécution(s) de pipeline.",
        lifecycle="termine", health="operationnel", artifact_ref=".",
    )


if __name__ == "__main__":
    main()
