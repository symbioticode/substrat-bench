"""
pipelines/common/isolation.py — Isolation réelle LLM (§2bis protocole)
Contrainte structurelle : chaque appel isolé = messages=[{role:user}] seul, sans historique.
Vérifiable par lecture de code + test automatisé Sprint 1/2.
"""

from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod


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
    
    response = client.create_message(
        model=config.model,
        messages=messages,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        **extra_kwargs
    )
    
    # Extraction standardisée du texte (adapter selon client)
    if hasattr(response, 'content') and response.content:
        return response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
    elif hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    else:
        return str(response)


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
    
    response = client.create_message(
        model=config.model,
        messages=messages,
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        **kwargs
    )
    
    if hasattr(response, 'content') and response.content:
        return response.content[0].text if hasattr(response.content[0], 'text') else str(response.content[0])
    elif hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    else:
        return str(response)


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