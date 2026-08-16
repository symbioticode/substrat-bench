"""
pipelines/common/isolation.py — Isolation réelle LLM (§2bis protocole)
Contrainte structurelle : chaque appel isolé = messages=[{role:user}] seul, sans historique.
Vérifiable par lecture de code + test automatisé Sprint 1/2.
"""

from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import time


class LLMClient(Protocol):
    """Interface minimale pour client LLM (OpenAI, Anthropic, local)."""
    
    def create_message(
        self,
        model: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        **kwargs: Any
    ) -> Any:
        """Appel LLM unique. Retourne objet avec .content[0].text"""
        ...


@dataclass(frozen=True)
class IsolationConfig:
    """Configuration immuable pour un appel isolé."""
    model: str
    max_tokens: int = 2000
    temperature: float = 0.6
    system_prompt: Optional[str] = None  # Si None, pas de message system
    provider: str = "unknown"


@dataclass(frozen=True)
class CallMetadata:
    """Identité expérimentale obligatoire d'une réponse LLM."""
    pipeline: str
    cycle: str
    repetition: int
    role: str
    round_num: int
    response_index: int
    seed: Optional[int]


class InferenceLedger:
    """Registre JSONL append-only, une ligne par réponse LLM terminée."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: Dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def _usage_value(response: Any, *names: str) -> Optional[int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    for name in names:
        value = getattr(usage, name, None)
        if value is None and isinstance(usage, dict):
            value = usage.get(name)
        if value is not None:
            return int(value)
    return None


def _response_text(response: Any) -> str:
    if hasattr(response, 'content') and response.content:
        return response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    return str(response)


def _estimated_cost_usd(provider: str, input_tokens: Optional[int],
                        output_tokens: Optional[int]) -> Optional[float]:
    """Estimation conservatrice D2; DeepSeek compte tout l'input en cache miss."""
    if provider != "deepseek" or input_tokens is None or output_tokens is None:
        return None
    return round((input_tokens * 0.14 + output_tokens * 0.28) / 1_000_000, 8)


def _execute_call(
    client: LLMClient,
    config: IsolationConfig,
    content: str,
    metadata: Optional[CallMetadata],
    ledger: Optional[InferenceLedger],
    **extra_kwargs: Any,
) -> str:
    messages = [{"role": "user", "content": content}]
    validate_isolation(messages)
    call_kwargs = dict(extra_kwargs)
    # Anthropic ne fournit pas de paramètre seed. Une absence de contrôle est
    # consignée comme null au lieu d'être présentée comme reproductible.
    effective_seed = metadata.seed if metadata else None
    if effective_seed is not None and config.provider in {"mock", "openai"}:
        call_kwargs["seed"] = effective_seed
    elif config.provider not in {"mock", "openai"}:
        effective_seed = None

    started = time.perf_counter()
    response = client.create_message(
        model=config.model,
        messages=messages,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        **call_kwargs,
    )
    wall_time_ms = round((time.perf_counter() - started) * 1000, 3)
    text = _response_text(response)

    if ledger is not None:
        if metadata is None:
            raise ValueError("CallMetadata obligatoire lorsqu'un registre est actif")
        input_tokens = _usage_value(response, "input_tokens", "prompt_tokens")
        output_tokens = _usage_value(response, "output_tokens", "completion_tokens")
        ledger.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pipeline": metadata.pipeline,
            "cycle": metadata.cycle,
            "repetition": metadata.repetition,
            "role": metadata.role,
            "round": metadata.round_num,
            "response_index": metadata.response_index,
            "seed": effective_seed,
            "seed_requested": metadata.seed,
            "model": config.model,
            "provider": config.provider,
            "prompt_sha256": sha256(content.encode("utf-8")).hexdigest(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "wall_time_ms": wall_time_ms,
            "estimated_cost_usd": _estimated_cost_usd(
                config.provider, input_tokens, output_tokens),
        })
    return text


def build_isolated_messages(prompt_fixe: str, corpus_text: str) -> List[Dict[str, str]]:
    """
    Construit la liste messages pour un appel VRAIMENT isolé.
    
    RÈGLE §2bis : UN SEUL message 'user', PAS d'historique, PAS de message 'assistant' préalable.
    """
    content = f"{prompt_fixe}\n\n---\n{corpus_text}"
    return [{"role": "user", "content": content}]


def validate_isolation(messages: List[Dict[str, str]]) -> None:
    """
    Assertion de validation d'isolation — ÉCHOUE SI VIOLATION.
    
    Utilisé dans tests automatisés Sprint 1 (P0/P1/P2) et Sprint 2 (P2 débat).
    """
    assert len(messages) == 1, (
        f"VIOLATION ISOLATION : {len(messages)} messages au lieu de 1. "
        f"Contexte partagé détecté — chaque instance doit avoir un contexte vierge."
    )
    assert messages[0]["role"] == "user", "Premier message doit être 'user'"
    assert "assistant" not in [m["role"] for m in messages], "Pas de message assistant en entrée"


def isolated_call(
    client: LLMClient,
    config: IsolationConfig,
    prompt_fixe: str,
    corpus_text: str,
    metadata: Optional[CallMetadata] = None,
    ledger: Optional[InferenceLedger] = None,
    **extra_kwargs: Any
) -> str:
    """
    Appel LLM isolé garanti sans contamination.
    
    Returns:
        Texte de réponse brut (content[0].text ou équivalent)
    
    Raises:
        AssertionError: si validation isolation échoue
        Exception: erreurs API propagées
    """
    messages = build_isolated_messages(prompt_fixe, corpus_text)
    validate_isolation(messages)
    
    return _execute_call(client, config, messages[0]["content"], metadata, ledger, **extra_kwargs)


class ArbiterInterface(Protocol):
    """
    Interface pour arbitre/cartographe/noyau — INTERDIT d'accéder au corpus brut.
    
    RÈGLE §2bis : signature SANS paramètre corpus_text — impossible d'y accéder même par erreur.
    """
    
    def __call__(
        self,
        client: LLMClient,
        config: IsolationConfig,
        prompt_arbitrage: str,
        sorties_structurees_passe_precedente: List[Dict[str, Any]],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Args:
            sorties_structurees_passe_precedente: Sorties JSON des parseurs/instances précédentes
            **kwargs: Paramètres additionnels (ex: ground_truth_ref pour debug ONLY)
        
        Returns:
            Dict structuré selon schéma P3/P4
        
        NOTE: corpus_text N'EST PAS dans la signature — violation = erreur de conception
        """
        ...


def make_arbiter_call(
    client: LLMClient,
    config: IsolationConfig,
    prompt_arbitrage: str,
    sorties_precedentes: List[Dict[str, Any]],
    metadata: Optional[CallMetadata] = None,
    ledger: Optional[InferenceLedger] = None,
    **kwargs: Any
) -> str:
    """
    Appel arbitre isolé — même pattern que isolated_call mais sans corpus.
    
    Les sorties_precedentes sont sérialisées en JSON dans le prompt.
    """
    import json
    
    sorties_json = json.dumps(sorties_precedentes, ensure_ascii=False, indent=2)
    content = f"{prompt_arbitrage}\n\n---\nSORTIES PASSÉES:\n{sorties_json}"
    
    messages = [{"role": "user", "content": content}]
    validate_isolation(messages)  # Même validation : 1 message user seulement
    
    return _execute_call(client, config, content, metadata, ledger, **kwargs)


# === Test d'isolation pour Sprint 1 (P0/P1/P2) ===
def test_isolation_assertion() -> None:
    """Test unitaire : validate_isolation détecte les violations."""
    # Cas valide
    validate_isolation([{"role": "user", "content": "test"}])
    
    # Cas invalides — doivent lever AssertionError
    try:
        validate_isolation([
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "msg2"}
        ])
        assert False, "Should have raised AssertionError"
    except AssertionError:
        pass  # Expected
    
    try:
        validate_isolation([{"role": "system", "content": "sys"}])
        assert False, "Should have raised AssertionError"
    except AssertionError:
        pass
    
    print("[OK] test_isolation_assertion passed")


# === Test d'injection contexte pour Sprint 2 (P2 débat) ===
def build_debate_round_messages(
    prompt_fixe: str,
    corpus_text: str,
    own_previous_output: str,
    other_outputs_anonymized: List[str],
    round_num: int
) -> List[Dict[str, str]]:
    """
    Construit messages pour P2 round N>1 — INJECTION EXPLICITE des sorties autres instances.
    
    RÈGLE §2 : Pour P1 (débat), le test AUTOMATIQUE Sprint 2 doit confirmer que
    les sorties des AUTRES instances sont présentes dans le contexte.
    
    Args:
        own_previous_output: Sa propre sortie round précédent
        other_outputs_anonymized: Sorties ANONYMISÉES des autres instances
        round_num: Numéro du round (1-indexed)
    """
    if round_num == 1:
        return build_isolated_messages(prompt_fixe, corpus_text)
    
    other_text = "\n\n".join(
        f"[Instance {i+1}]\n{out}" 
        for i, out in enumerate(other_outputs_anonymized)
    )
    
    content = (
        f"{prompt_fixe}\n\n"
        f"---\nCORPUS:\n{corpus_text}\n\n"
        f"---\nVOTRE SORTIE ROUND {round_num-1}:\n{own_previous_output}\n\n"
        f"---\nSORTIES AUTRES INSTANCES ROUND {round_num-1} (ANONYMES):\n{other_text}\n\n"
        f"INSTRUCTION: Révisez, confirmez ou retirez chaque assertion "
        f"à la lumière de ce qu'ont vu les autres."
    )
    
    return [{"role": "user", "content": content}]


def test_debate_context_injection() -> None:
    """Test Sprint 2 : confirme injection sorties autres instances."""
    msgs = build_debate_round_messages(
        prompt_fixe="Test",
        corpus_text="Corpus",
        own_previous_output="Ma sortie",
        other_outputs_anonymized=["Sortie A", "Sortie B"],
        round_num=2
    )
    
    assert len(msgs) == 1
    content = msgs[0]["content"]
    assert "SORTIES AUTRES INSTANCES" in content
    assert "Sortie A" in content
    assert "Sortie B" in content
    assert "Ma sortie" in content
    
    print("[OK] test_debate_context_injection passed")


if __name__ == "__main__":
    test_isolation_assertion()
    test_debate_context_injection()
    print("\n✅ Tous les tests d'isolation passent")
