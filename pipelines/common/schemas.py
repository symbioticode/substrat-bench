"""
pipelines/common/schemas.py — Schémas de sortie structurés P3/P4
Inspirés DiAML (ISO 24617-2) mais minimalistes pour ETAU/SECS.
Validation M06 (traçabilité) + confiance graduée.
"""

from typing import List, Dict, Any, Optional, Literal, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json


def iter_json_objects(text: str, limit: Optional[int] = None):
    """Extrait des objets JSON successifs, compacts ou indentés sur plusieurs lignes."""
    decoder = json.JSONDecoder()
    cursor = 0
    yielded = 0
    while cursor < len(text) and (limit is None or yielded < limit):
        start = text.find("{", cursor)
        if start < 0:
            return
        try:
            value, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            cursor = start + 1
            continue
        values = value.get("assertions") if (
            isinstance(value, dict) and "text" not in value
            and isinstance(value.get("assertions"), list)
        ) else [value]
        for item in values:
            if isinstance(item, dict):
                yield item
                yielded += 1
                if limit is not None and yielded >= limit:
                    break
        cursor = end


class DialogueAct(str, Enum):
    """Fonctions communicatives core (sous-ensemble DiAML ISO 24617-2)."""
    # General-purpose (utilisables dans toute dimension)
    INFORM = "Inform"
    REQUEST = "Request"
    CONFIRM = "Confirm"
    DISAGREE = "Disagree"
    AGREE = "Agree"
    CORRECT = "Correct"          # Correction d'une assertion antérieure
    RETRACT = "Retract"          # Rétractation explicite
    QUESTION = "Question"
    ANSWER = "Answer"
    # Dimension-specific
    TURN_ACCEPT = "TurnAccept"
    TURN_GIVE = "TurnGive"
    STALL = "Stall"
    AUTO_POSITIVE = "AutoPositive"
    AUTO_NEGATIVE = "AutoNegative"
    # ETAU/SECS extensions
    HYPOTHESIZE = "Hypothesize"  # "Il semble que..." (β=N honnête)
    PROJECT = "Project"          # Projection non vérifiée (dérive épistémique)
    FLAG_GAP = "FlagGap"         # Lacune silencieuse signalée
    FLAG_AMBIGUITY = "FlagAmbiguity"  # Ambiguïté genuine signalée


class ConfidenceLevel(str, Enum):
    """Niveaux de confiance P3/P4."""
    # P3 (allégé) : binaire
    FORT = "FORT"
    FAIBLE = "FAIBLE"
    # P4 (complet) : ternaire
    PROBABLE = "PROBABLE"


class EpistemicState(str, Enum):
    """État épistémique type Belnap (pour traçabilité dérives)."""
    T = "T"      # True / soutenu
    F = "F"      # False / contredit
    B = "B"      # Both / conflit (CONTRADICTION_INTER)
    N = "N"      # Neither / ignorance (LACUNE_SILENCIEUSE, AMBIGU_GENUINE)


@dataclass
class SourceRef:
    """Référence source obligatoire (§1bis) — niveau fil ou tour."""
    session_id: str
    tour_n: int
    locuteur: Optional[str] = None
    # Pour traçabilité ligne (Option A) — non utilisée par défaut (Option B)
    char_start: Optional[int] = None
    char_end: Optional[int] = None


@dataclass
class ReasoningTrace:
    """Traçabilité du raisonnement (pour M06)."""
    steps: List[str] = field(default_factory=list)
    # Pour arbitre P3/P4 : quel cluster a prévalu et pourquoi
    coherence_check: Optional[str] = None
    conflicting_evidence: List[str] = field(default_factory=list)


@dataclass
class StructuredAssertion:
    """
    Assertion structurée sortie parseur (P3/P4 passe 1).
    CHAMP source_ref OBLIGATOIRE (§1bis) — même pour P0/P1/P2.
    PAS de champ confidence au niveau parseur (assigné par arbitre seulement).
    """
    # Contenu
    text: str
    dialogue_act: DialogueAct
    # Traçabilité obligatoire
    source_ref: SourceRef
    epistemic_state: EpistemicState = EpistemicState.N
    
    # Raisonnement (optionnel pour parseurs, requis pour arbitres)
    reasoning: Optional[ReasoningTrace] = None
    
    # Métadonnées
    parseur_id: str = ""
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dialogue_act"] = self.dialogue_act.value
        d["epistemic_state"] = self.epistemic_state.value
        d["source_ref"] = asdict(self.source_ref)
        if self.reasoning:
            d["reasoning"] = asdict(self.reasoning) if isinstance(self.reasoning, ReasoningTrace) else self.reasoning
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StructuredAssertion":
        d = d.copy()
        d["dialogue_act"] = DialogueAct(d["dialogue_act"])
        d["epistemic_state"] = EpistemicState(d["epistemic_state"])
        d["source_ref"] = SourceRef(**d["source_ref"])
        if d.get("reasoning"):
            if isinstance(d["reasoning"], dict):
                d["reasoning"] = ReasoningTrace(**d["reasoning"])
            elif isinstance(d["reasoning"], str):
                d["reasoning"] = ReasoningTrace(steps=[d["reasoning"]])
        return cls(**d)


@dataclass
class ArbitratedAssertion(StructuredAssertion):
    """
    Assertion après arbitrage (P3/P4 sortie finale).
    AJOUTE confidence (assignée PAR L'ARBITRE seulement, jamais parseur).
    """
    confidence: ConfidenceLevel = ConfidenceLevel.FAIBLE
    # Pour P4 : niveau de cohérence (N/N, (N-1)/N, 1/N + argument autonome)
    coherence_level: Optional[str] = None  # "FULL", "MAJORITY", "SINGLETON_AUTONOME"
    
    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d["confidence"] = self.confidence.value
        if self.coherence_level:
            d["coherence_level"] = self.coherence_level
        return d


@dataclass
class ParseurOutput:
    """Sortie complète d'un parseur isolé (P3/P4 round 1)."""
    parseur_id: str
    assertions: List[StructuredAssertion]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_jsonl(self) -> str:
        lines = []
        for a in self.assertions:
            d = a.to_dict()
            d["parseur_id"] = self.parseur_id
            lines.append(json.dumps(d, ensure_ascii=False))
        return "\n".join(lines)
    
    @classmethod
    def from_jsonl(cls, text: str, parseur_id: str) -> "ParseurOutput":
        assertions = []
        for data in iter_json_objects(text, limit=32):
            try:
                assertions.append(StructuredAssertion.from_dict(data))
            except (KeyError, ValueError, TypeError):
                # Une entrée mal formée ne doit pas invalider les objets valides
                # qui suivent dans la même réponse brute.
                continue
        return cls(parseur_id=parseur_id, assertions=assertions)


@dataclass
class ArbitreOutput:
    """Sortie arbitre unique (P3) ou noyau cohérence (P4 round 3)."""
    assertions: List[ArbitratedAssertion]
    non_convergence_zones: List[Dict[str, Any]] = field(default_factory=list)
    # Zones où arbitre signale "pas de convergence" = ambiguïté genuine (M07)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_jsonl(self) -> str:
        lines = []
        for a in self.assertions:
            lines.append(json.dumps(a.to_dict(), ensure_ascii=False))
        for zone in self.non_convergence_zones:
            lines.append(json.dumps({"type": "non_convergence", **zone}, ensure_ascii=False))
        return "\n".join(lines)


# Schémas pour validation (optionnel : jsonschema)
PARSEUR_SCHEMA = {
    "type": "object",
    "required": ["parseur_id", "assertions"],
    "properties": {
        "parseur_id": {"type": "string"},
        "assertions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["text", "dialogue_act", "source_ref"],
                "properties": {
                    "text": {"type": "string"},
                    "dialogue_act": {"type": "string", "enum": [e.value for e in DialogueAct]},
                    "epistemic_state": {"type": "string", "enum": [e.value for e in EpistemicState]},
                    "source_ref": {
                        "type": "object",
                        "required": ["session_id", "tour_n"],
                        "properties": {
                            "session_id": {"type": "string"},
                            "tour_n": {"type": "integer"},
                            "locuteur": {"type": ["string", "null"]}
                        }
                    },
                    "reasoning": {"type": ["object", "null"]}
                }
            }
        }
    }
}

ARBITRE_SCHEMA = {
    "type": "object",
    "required": ["assertions"],
    "properties": {
        "assertions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["text", "dialogue_act", "source_ref", "confidence"],
                "properties": {
                    "text": {"type": "string"},
                    "dialogue_act": {"type": "string", "enum": [e.value for e in DialogueAct]},
                    "epistemic_state": {"type": "string", "enum": [e.value for e in EpistemicState]},
                    "source_ref": {
                        "type": "object",
                        "required": ["session_id", "tour_n"],
                        "properties": {
                            "session_id": {"type": "string"},
                            "tour_n": {"type": "integer"}
                        }
                    },
                    "confidence": {"type": "string", "enum": [e.value for e in ConfidenceLevel]},
                    "coherence_level": {"type": ["string", "null"]},
                    "reasoning": {"type": ["object", "null"]}
                }
            }
        },
        "non_convergence_zones": {"type": "array"}
    }
}


def validate_output(output: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validation simple sans dépendance jsonschema (pour Sprint 3)."""
    errors = []
    
    def check_required(obj: Dict, required: List[str], path: str = ""):
        for field in required:
            if field not in obj:
                errors.append(f"{path}.{field}: champ requis manquant")
    
    check_required(output, schema.get("required", []))
    
    # Validation basique assertions
    if "assertions" in output:
        for i, a in enumerate(output["assertions"]):
            check_required(a, ["text", "dialogue_act", "source_ref"], f"assertions[{i}]")
            if "source_ref" in a:
                check_required(a["source_ref"], ["session_id", "tour_n"], f"assertions[{i}].source_ref")
            if "confidence" in schema.get("properties", {}).get("assertions", {}).get("items", {}).get("required", []):
                if "confidence" not in a:
                    errors.append(f"assertions[{i}].confidence: requis pour sortie arbitre")
    
    return len(errors) == 0, errors


# === Test unitaire Sprint 3 ===
def test_schemas():
    """Test sérialisation/désérialisation schémas."""
    # Parseur output
    src = SourceRef(session_id="s1", tour_n=5, locuteur="Alice")
    assertion = StructuredAssertion(
        text="Le budget est de 10M€",
        dialogue_act=DialogueAct.INFORM,
        epistemic_state=EpistemicState.T,
        source_ref=src,
        parseur_id="parseur_1"
    )
    
    d = assertion.to_dict()
    assert d["dialogue_act"] == "Inform"
    assert d["source_ref"]["session_id"] == "s1"
    
    restored = StructuredAssertion.from_dict(d)
    assert restored.text == assertion.text
    assert restored.source_ref.session_id == "s1"
    
    # Arbitre output
    arb_assertion = ArbitratedAssertion(
        text="Le budget est de 10M€",
        dialogue_act=DialogueAct.INFORM,
        epistemic_state=EpistemicState.T,
        source_ref=src,
        confidence=ConfidenceLevel.FORT,
        coherence_level="FULL"
    )
    
    arb_d = arb_assertion.to_dict()
    assert arb_d["confidence"] == "FORT"
    assert arb_d["coherence_level"] == "FULL"
    
    print("[OK] test_schemas passed")


def test_validation():
    """Test validation sortie."""
    valid_output = {
        "assertions": [{
            "text": "Test",
            "dialogue_act": "Inform",
            "source_ref": {"session_id": "s1", "tour_n": 1},
            "confidence": "FORT"
        }]
    }
    
    ok, errors = validate_output(valid_output, ARBITRE_SCHEMA)
    assert ok, f"Valid output rejected: {errors}"
    
    invalid_output = {
        "assertions": [{
            "text": "Test",
            "dialogue_act": "Inform",
            "source_ref": {"session_id": "s1"}  # tour_n manquant
        }]
    }
    
    ok, errors = validate_output(invalid_output, ARBITRE_SCHEMA)
    assert not ok
    assert any("tour_n" in e for e in errors)
    
    print("[OK] test_validation passed")


if __name__ == "__main__":
    test_schemas()
    test_validation()
    print("\n✅ Tests schémas passent")
