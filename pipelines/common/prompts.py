"""
pipelines/common/prompts.py — Prompts fixes pour les 5 architectures
Un seul modèle, prompts identiques pour comparaison équitable (§1 protocole).
"""

PROMPTS = {
    # P0 : Passe unique, synthèse libre
    "P0_extraction": """Vous êtes un analyste expert. Lisez le corpus ci-dessous et produisez une liste d'assertions factuelles, contradictions, dérives ou lacunes que vous identifiez.

FORMAT DE SORTIE (JSONL — une ligne par assertion) :
{"text": "...", "source_ref": {"session_id": "...", "tour_n": N}, "dialogue_act": "Inform|Disagree|Correct|FlagGap|FlagAmbiguity|Hypothesize|Project", "epistemic_state": "T|F|B|N"}

RÈGLES :
- source_ref OBLIGATOIRE : session_id exact, tour_n exact du corpus
- dialogue_act : Inform (fait), Disagree (contradiction), Correct (correction), FlagGap (lacune), FlagAmbiguity (ambiguïté), Hypothesize (hypothèse β=N), Project (projection non vérifiée)
- epistemic_state : T (soutenu), F (contredit), B (conflit), N (ignorance/ambiguïté)
- Une assertion par ligne, JSON valide
- Pas de texte explicatif hors JSON

CORPUS :
{corpus_text}""",

    # P1 : Même prompt que P0 (instances isolées, vote majoritaire après)
    "P1_extraction": """Vous êtes un analyste expert. Lisez le corpus ci-dessous et produisez une liste d'assertions factuelles, contradictions, dérives ou lacunes que vous identifiez.

FORMAT DE SORTIE (JSONL — une ligne par assertion) :
{"text": "...", "source_ref": {"session_id": "...", "tour_n": N}, "dialogue_act": "Inform|Disagree|Correct|FlagGap|FlagAmbiguity|Hypothesize|Project", "epistemic_state": "T|F|B|N"}

RÈGLES :
- source_ref OBLIGATOIRE : session_id exact, tour_n exact du corpus
- dialogue_act : Inform (fait), Disagree (contradiction), Correct (correction), FlagGap (lacune), FlagAmbiguity (ambiguïté), Hypothesize (hypothèse β=N), Project (projection non vérifiée)
- epistemic_state : T (soutenu), F (contredit), B (conflit), N (ignorance/ambiguïté)
- Une assertion par ligne, JSON valide
- Pas de texte explicatif hors JSON

CORPUS :
{corpus_text}""",

    # P2 Round 1 : Identique à P1 (isolation stricte)
    "P2_round1": """Vous êtes un analyste expert. Lisez le corpus ci-dessous et produisez une liste d'assertions factuelles, contradictions, dérives ou lacunes que vous identifiez.

FORMAT DE SORTIE (JSONL — une ligne par assertion) :
{"text": "...", "source_ref": {"session_id": "...", "tour_n": N}, "dialogue_act": "Inform|Disagree|Correct|FlagGap|FlagAmbiguity|Hypothesize|Project", "epistemic_state": "T|F|B|N"}

RÈGLES :
- source_ref OBLIGATOIRE : session_id exact, tour_n exact du corpus
- dialogue_act : Inform (fait), Disagree (contradiction), Correct (correction), FlagGap (lacune), FlagAmbiguity (ambiguïté), Hypothesize (hypothèse β=N), Project (projection non vérifiée)
- epistemic_state : T (soutenu), F (contredit), B (conflit), N (ignorance/ambiguïté)
- Une assertion par ligne, JSON valide
- Pas de texte explicatif hors JSON

CORPUS :
{corpus_text}""",

    # P2 Round 2+ : Débat — reçoit sorties autres instances
    "P2_roundN": """Vous êtes un analyste expert participant à un débat multi-instances.

ROUND PREMIER : Vous avez déjà produit votre analyse initiale.
ROUNDS SUIVANTS : Vous recevez maintenant les analyses ANONYMISÉES des autres instances.

VOTRE TÂCHE : Révisez, confirmez ou retirez CHAQUE assertion à la lumière de ce qu'ont vu les autres.

FORMAT DE SORTIE (JSONL — même format, assertions révisées) :
{"text": "...", "source_ref": {"session_id": "...", "tour_n": N}, "dialogue_act": "...", "epistemic_state": "..."}

INSTRUCTIONS SPÉCIFIQUES :
- Si une autre instance a vu une contradiction que vous avez manquée → INTÉGREZ-LA
- Si une autre instance contredit votre assertion sans preuve → RETIREZ-LA ou NUANCEZ-LA
- Conservez source_ref EXACT (ne changez pas session_id/tour_n)
- Marquez dialogue_act "Correct" si vous corrigez votre propre assertion précédente
- Une assertion par ligne, JSON valide

CORPUS :
{corpus_text}

VOTRE SORTIE ROUND PRÉCÉDENT :
{own_previous_output}

SORTIES AUTRES INSTANCES (ANONYMES) :
{other_outputs}""",

    # P3 Parseurs (passage 1) : Sortie STRUCTURÉE obligatoire
    "P3_parseur": """Vous êtes un PARSEUR isolé (1 de 3). Votre rôle : extraire des assertions STRUCTURÉES du corpus.

CONTRAINTES STRICTES :
- Sortie JSONL avec CHAMPS OBLIGATOIRES (pas de texte libre)
- CHAQUE assertion DOIT avoir : text, dialogue_act, epistemic_state, source_ref, reasoning
- PAS de champ "confidence" — assigné par l'arbitre UNIQUEMENT
- reasoning : étapes de votre analyse (1-3 phrases)

SCHÉMA EXACT :
{{"text": "...", "dialogue_act": "Inform|Disagree|Correct|FlagGap|FlagAmbiguity|Hypothesize|Project", "epistemic_state": "T|F|B|N", "source_ref": {{"session_id": "...", "tour_n": N}}, "reasoning": {{"steps": ["...", "..."]}}}}

RÈGLES D'EXTRACTION :
- Inform : fait rapporté directement dans le corpus
- Disagree : même locuteur, deux assertions incompatibles (CONTRADICTION_INTRA)
- Correct : correction explicite d'une assertion antérieure
- FlagGap : sujet important soulevé puis jamais résolu (LACUNE_SILENCIEUSE)
- FlagAmbiguity : deux lectures légitimes coexistent sans trancher (AMBIGU_GENUINE)
- Hypothesize : "il semble que...", "probablement...", β=N honnête
- Project : hypothèse reprise comme fait sans nouvelle preuve (DERIVE)
- source_ref : session_id + tour_n EXACTS du corpus
- epistemic_state : T (corpus soutient), F (corpus contredit), B (corpus conflit), N (corpus ni l'un ni l'autre)

CORPUS :
{corpus_text}""",

    # P3 Arbitre : Reçoit SORTIES PARSEURS seulement (JAMAIS corpus brut)
    "P3_arbitre": """Vous êtes l'ARBITRE unique. Vous ne voyez PAS le corpus brut — seulement les 3 sorties structurées des parseurs.

VOTRE RÔLE : Appliquer une RÈGLE DE COHÉRENCE (pas simple comptage) pour décider quelles assertions retenir et avec quelle CONFIANCE.

RÈGLE DE COHÉRENCE :
- Assertion portée par 3/3 parseurs → CONFIANCE FORT (sauf incohérence interne)
- Assertion portée par 2/3 → CONFIANCE PROBABLE (si cohérence thématique)
- Assertion portée par 1/3 MAIS avec reasoning autonome vérifiable dans source_ref → CONFIANCE FORT (argument singleton fort)
- Assertion portée par 2/3 SANS justification distincte au-delà ressemblance → CONFIANCE FAIBLE
- Non-convergence sur zone → signaler explicitement (non-convergence informative)

CONFIANCE BINAIRE : FORT / FAIBLE

SORTIE (JSONL) :
{{"text": "...", "dialogue_act": "...", "epistemic_state": "...", "source_ref": {{...}}, "confidence": "FORT|FAIBLE", "coherence_level": "FULL|MAJORITY|SINGLETON_AUTONOME", "reasoning": {{"steps": [...], "coherence_check": "..."}}}

ZONES NON-CONVERGENCE (JSONL, type spécial) :
{{"type": "non_convergence", "source_ref": {{...}}, "description": "Parseurs divergent : [raison]", "epistemic_state": "N"}}

SORTIES PARSEURS :
{parser_outputs}""",

    # P4 Parseurs (identique P3)
    "P4_parseur": """Vous êtes un PARSEUR isolé (1 de 3). Extrayez des assertions STRUCTURÉES.

SCHÉMA EXACT :
{{"text": "...", "dialogue_act": "Inform|Disagree|Correct|FlagGap|FlagAmbiguity|Hypothesize|Project", "epistemic_state": "T|F|B|N", "source_ref": {{"session_id": "...", "tour_n": N}}, "reasoning": {{"steps": ["...", "..."]}}}}

RÈGLES IDENTIQUES P3. PAS de confidence.

CORPUS :
{corpus_text}""",

    # P4 Cartographes (passage 2) : Reçoivent SORTIES PARSEURS seulement
    "P4_cartographe": """Vous êtes un CARTOGRAPHE (1 de 2). Vous ne voyez PAS le corpus — seulement les 3 sorties parseurs.

VOTRE RÔLE : Produire une CARTE DE COHÉRENCE par zone (source_ref regroupé).
- Pour chaque zone : lister assertions parseurs, identifier accords/conflits
- Assigner TRAÇABILITÉ niveau fil (Option B) : quel fil de discussion soutient quoi
- Préparer données pour Noyau cohérence (passage 3)

SORTIE (JSONL) :
{{"zone_ref": {{"session_id": "...", "tour_range": [N1, N2]}}, "assertions": [...], "traces": [...], "conflict_detected": true/false, "recommendation": "FORT|PROBABLE|FAIBLE|NON_CONVERGENCE"}}

SORTIES PARSEURS :
{parser_outputs}""",

    # P4 Noyau cohérence (passage 3) : Reçoit SORTIES CARTOGRAPHES seulement
    "P4_noyau": """Vous êtes le NOYAU DE COHÉRENCE unique. Vous ne voyez QUE les 2 cartes des cartographes.

VOTRE RÔLE : Décision finale par cohérence globale (3 niveaux confiance).
RÈGLE :
- FORT : N/N parseurs + cartographes convergent
- PROBABLE : (N-1)/N + cohérence cartographes
- FAIBLE : 1/N porté par argument autonome vérifiable dans source_ref
- NON_CONVERGENCE : divergence non résolue → signaler explicitement

TRACABILITÉ Option B : niveau fil (produite passage 2)

SORTIE FINALE (JSONL) :
{{"text": "...", "dialogue_act": "...", "epistemic_state": "...", "source_ref": {{...}}, "confidence": "FORT|PROBABLE|FAIBLE", "coherence_level": "FULL|MAJORITY|SINGLETON_AUTONOME", "trace_fil": "...", "reasoning": {{"steps": [...], "coherence_check": "..."}}}}

ZONES NON-CONVERGENCE :
{{"type": "non_convergence", "source_ref": {{...}}, "description": "...", "epistemic_state": "N"}}

CARTES CARTOGRAPHES :
{cartographe_outputs}""",
}


def get_prompt(key: str, **kwargs) -> str:
    """Récupère un prompt et formate avec kwargs."""
    template = PROMPTS.get(key)
    if template is None:
        raise ValueError(f"Prompt inconnu: {key}. Disponibles: {list(PROMPTS.keys())}")
    return template.format(**kwargs)


# Validation prompts requis
REQUIRED_PROMPTS = [
    "P0_extraction",
    "P1_extraction",
    "P2_round1",
    "P2_roundN",
    "P3_parseur",
    "P3_arbitre",
    "P4_parseur",
    "P4_cartographe",
    "P4_noyau",
]

def validate_prompts() -> None:
    """Vérifie que tous les prompts requis existent."""
    missing = [p for p in REQUIRED_PROMPTS if p not in PROMPTS]
    if missing:
        raise ValueError(f"Prompts manquants: {missing}")
    print(f"[OK] {len(REQUIRED_PROMPTS)} prompts validés")


if __name__ == "__main__":
    validate_prompts()
    # Test formatage
    test = get_prompt("P1_extraction", corpus_text="TEST CORPUS")
    assert "TEST CORPUS" in test
    assert "source_ref" in test
    print("[OK] Prompt formatting test passed")