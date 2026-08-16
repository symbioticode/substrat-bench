"""Personas normatives du Cycle B, chargées verbatim depuis l'Annexe A."""

from pathlib import Path

PERSONA_FILES = {
    "verificateur_coherence": "persona_verificateur.md",
    "traceur_provenance": "persona_traceur.md",
    "cartographe_fils_ouverts": "persona_cartographe.md",
}
PERSONA_DIR = Path(__file__).parents[2] / "prompts" / "personas"
PERSONA_POSTURES = {
    name: (PERSONA_DIR / filename).read_text(encoding="utf-8").strip()
    for name, filename in PERSONA_FILES.items()
}
PERSONA_ORDER = tuple(PERSONA_FILES)


def get_persona_for_instance(instance_id: str) -> str:
    try:
        index = int(instance_id.rsplit("_", 1)[-1])
    except ValueError:
        index = 0
    return PERSONA_ORDER[index % len(PERSONA_ORDER)]


def build_persona_injection(persona_name: str) -> str:
    return f"\n\n=== PERSONA ASSIGNÉE ===\n{PERSONA_POSTURES[persona_name]}\n========================\n"


def get_persona_description(persona_name: str) -> str:
    return PERSONA_POSTURES[persona_name]


PERSONA_INCIDENT_COVERAGE = {
    "verificateur_coherence": ["CONTRADICTION_INTRA", "CONTRADICTION_INTER"],
    "traceur_provenance": ["NON_ETAYE", "DERIVE"],
    "cartographe_fils_ouverts": ["LACUNE_SILENCIEUSE", "AMBIGU_GENUINE"],
}
