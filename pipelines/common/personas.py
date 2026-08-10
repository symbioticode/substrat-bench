"""Personas de lecture du Cycle B (protocole v0.2.2, annexe A)."""

PERSONA_POSTURES = {
    "VERIFICATEUR_COHERENCE": (
        "Toute affirmation a un précédent à confronter. Détectez les "
        "contradictions intra/inter-session et citez les deux source_ref."
    ),
    "TRACEUR_PROVENANCE": (
        "D'où sait-on cela ? Signalez les affirmations non étayées et les "
        "hypothèses reprises comme faits, avec source_ref exact."
    ),
    "CARTOGRAPHE_FILS_OUVERTS": (
        "L'absence de clôture est un fait. Inventoriez les lacunes silencieuses "
        "et ambiguïtés genuinely non tranchées, avec source_ref exact."
    ),
}

_ORDER = tuple(PERSONA_POSTURES)


def get_persona_for_instance(instance_id: str):
    """Affectation déterministe 0/1/2, indépendante du nom du pipeline."""
    try:
        index = int(instance_id.rsplit("_", 1)[-1])
    except ValueError:
        index = 0
    return _ORDER[index % len(_ORDER)]


def build_persona_injection(persona_name: str) -> str:
    return f"\nPOSTURE DE LECTURE — {persona_name}:\n{PERSONA_POSTURES[persona_name]}\n"
