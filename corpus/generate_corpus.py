#!/usr/bin/env python3
"""Ajoute 24 incidents contrôlés au corpus D1 et produit la vérité terrain."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

SEED = 42
TYPES = ("CONTRADICTION_INTRA", "CONTRADICTION_INTER", "DERIVE",
         "NON_ETAYE", "LACUNE_SILENCIEUSE", "AMBIGU_GENUINE")
SCENARIOS = {
    "CONTRADICTION_INTRA": [
        ("Le pilote durera exactement six semaines.", "Le pilote durera exactement douze semaines.", "durée du pilote annoncée à six puis douze semaines"),
        ("Aucune donnée personnelle ne sera conservée.", "Les adresses nominatives seront conservées pendant un an.", "absence de données personnelles contredite par une conservation nominative"),
        ("Le rapport sera uniquement mensuel.", "Le rapport sera envoyé chaque semaine.", "fréquence du rapport annoncée mensuelle puis hebdomadaire"),
        ("Le système ne prendra jamais de décision.", "Le système choisira automatiquement les actions prioritaires.", "absence de décision automatique contredite par une priorisation autonome")],
    "CONTRADICTION_INTER": [
        ("Le budget maximal validé est de 2 000 unités.", "Le budget maximal validé est de 5 000 unités.", "deux instances donnent des budgets maximaux incompatibles"),
        ("La source est actualisée quotidiennement.", "La même source est actualisée une fois par trimestre.", "deux instances donnent des fréquences de source incompatibles"),
        ("Le consentement explicite est obligatoire avant collecte.", "La collecte commence sans consentement explicite.", "deux sessions prescrivent des règles de consentement incompatibles"),
        ("Le déploiement cible uniquement les commerces physiques.", "Le déploiement exclut tous les commerces physiques.", "deux sessions définissent des populations cibles incompatibles")],
    "DERIVE": [
        ("Il est possible que le pilote commence en septembre.", "Le pilote commencera en septembre, c'est confirmé.", "hypothèse de démarrage en septembre transformée en fait confirmé"),
        ("On suppose provisoirement que le taux de réponse sera de 20 %.", "Le taux de réponse est de 20 %.", "hypothèse provisoire de taux de réponse transformée en fait"),
        ("La conformité juridique reste à vérifier.", "La conformité juridique est acquise.", "vérification juridique ouverte transformée en conformité acquise"),
        ("Le modèle pourrait réduire la charge administrative.", "Le modèle réduit nécessairement la charge administrative.", "possibilité de réduction de charge transformée en certitude")],
    "NON_ETAYE": [
        ("Cette architecture réduira les coûts de 40 %.", "Aucune mesure ni source ne justifie les 40 % annoncés.", "réduction de coûts de 40 % annoncée sans mesure ni source"),
        ("Tous les utilisateurs préféreront une livraison quotidienne.", "Aucune enquête utilisateur n'a été menée.", "préférence universelle annoncée sans enquête"),
        ("Le marché doublera avant la fin de l'année.", "Aucune projection vérifiable n'accompagne cette prévision.", "doublement du marché annoncé sans projection vérifiable"),
        ("Cette méthode élimine entièrement les erreurs humaines.", "Aucun test ne démontre une élimination complète des erreurs.", "élimination complète des erreurs annoncée sans test")],
    "LACUNE_SILENCIEUSE": [
        ("Qui sera responsable si une recommandation automatisée cause une perte ?", "Passons maintenant au choix des couleurs de l'interface.", "responsabilité en cas de perte soulevée puis laissée sans réponse"),
        ("Comment détectera-t-on une source devenue obsolète ?", "Le prochain sujet concerne le format du rapport.", "détection des sources obsolètes soulevée puis abandonnée"),
        ("Quel est le plan de retour arrière si le fournisseur ferme ?", "Nous pouvons maintenant discuter du lancement commercial.", "retour arrière fournisseur soulevé puis non résolu"),
        ("Comment un utilisateur contestera-t-il une donnée incorrecte ?", "La discussion continue sur le prix de l'abonnement.", "contestation d'une donnée incorrecte soulevée puis ignorée")],
    "AMBIGU_GENUINE": [
        ("Le terme client peut désigner l'entreprise ou son représentant.", "Les deux interprétations restent compatibles avec le document.", "client désigne légitimement l'entreprise ou son représentant"),
        ("Une source récente peut signifier publiée récemment ou mise à jour récemment.", "Le protocole ne privilégie aucune de ces deux lectures.", "source récente a deux lectures légitimes non tranchées"),
        ("Actif peut qualifier un service démarré ou un service qui répond correctement.", "Les deux sens sont utilisés et aucun n'est défini comme prioritaire.", "actif désigne légitimement démarrage ou fonctionnement correct"),
        ("La réussite peut être évaluée par le gain financier ou par le temps libéré.", "Le mandat ne permet pas de choisir entre ces deux critères.", "réussite évaluée légitimement par argent ou temps sans arbitrage")],
}


def build_injections() -> tuple[list[dict], list[dict]]:
    injected, incidents = [], []
    rng = random.Random(SEED)
    ordered_types = list(TYPES)
    rng.shuffle(ordered_types)
    number = 0
    for incident_type in ordered_types:
        scenarios = list(SCENARIOS[incident_type])
        rng.shuffle(scenarios)
        for index, (origin, reprise, description) in enumerate(scenarios, start=1):
            number += 1
            # Identifiants opaques : aucune classe gold ne doit être visible
            # dans le corpus remis aux pipelines.
            base = f"s{number:03d}"
            if incident_type == "CONTRADICTION_INTER":
                origin_session, reprise_session = base + "a", base + "b"
                origin_speaker, reprise_speaker = "instance_alpha", "instance_beta"
            else:
                origin_session = reprise_session = base
                origin_speaker = reprise_speaker = "instance_alpha"
            reprise_turn = 2 if reprise_session == origin_session else 1
            injected.extend([
                {"session_id": origin_session, "tour_n": 1, "locuteur": origin_speaker, "texte": origin},
                {"session_id": reprise_session, "tour_n": reprise_turn, "locuteur": reprise_speaker, "texte": reprise}])
            incidents.append({"incident_id": f"INC-{number:02d}", "type": incident_type,
                              "source_ref_origine": {"session_id": origin_session, "tour_n": 1},
                              "source_ref_reprise": {"session_id": reprise_session, "tour_n": reprise_turn},
                              "description_courte": description})
    return injected, incidents


def interleave_sessions(source: list[dict], injected: list[dict]) -> list[dict]:
    """Mélange des blocs-session sans casser l'ordre interne des tours."""
    grouped: dict[str, list[dict]] = {}
    for row in source + injected:
        grouped.setdefault(row["session_id"], []).append(row)
    blocks = [sorted(rows, key=lambda row: row["tour_n"]) for rows in grouped.values()]
    random.Random(SEED + 1).shuffle(blocks)
    return [row for block in blocks for row in block]


def normalize_public_metadata(corpus: list[dict], incidents: list[dict]) -> tuple[list[dict], list[dict]]:
    """Retire toute métadonnée permettant de distinguer réel et synthétique."""
    sessions = sorted({row["session_id"] for row in corpus})
    opaque = [f"session_{index:03d}" for index in range(1, len(sessions) + 1)]
    random.Random(SEED + 2).shuffle(opaque)
    session_map = dict(zip(sessions, opaque))
    speaker_map = {
        "humain": "participant_1",
        "instance_eip": "participant_2",
        "instance_coherence": "participant_2",
        "instance_alpha": "participant_1",
        "instance_beta": "participant_2",
    }
    public = [{"session_id": session_map[row["session_id"]],
               "tour_n": row["tour_n"],
               "locuteur": speaker_map[row["locuteur"]],
               "texte": row["texte"]} for row in corpus]
    remapped_incidents = json.loads(json.dumps(incidents, ensure_ascii=False))
    for incident in remapped_incidents:
        for key in ("source_ref_origine", "source_ref_reprise"):
            incident[key]["session_id"] = session_map[incident[key]["session_id"]]
    return public, remapped_incidents


def compose_public_corpus(source: list[dict], injected: list[dict],
                          incidents: list[dict]) -> tuple[list[dict], list[dict]]:
    """Greffe les incidents dans deux conversations composites opaques."""
    source_blocks = {
        "session_001": [[row] for row in source if row["session_id"] == "lc_math"],
        "session_002": [[row] for row in source if row["session_id"] == "lc_coherence"],
    }
    incident_blocks: dict[str, list[list[dict]]] = {"session_001": [], "session_002": []}
    injection_by_ref = {
        (row["session_id"], row["tour_n"]): row for row in injected
    }
    for index, incident in enumerate(incidents):
        origin_target = "session_001" if index % 2 == 0 else "session_002"
        reprise_target = (
            "session_002" if origin_target == "session_001" else "session_001"
        ) if incident["type"] == "CONTRADICTION_INTER" else origin_target
        origin = injection_by_ref[(incident["source_ref_origine"]["session_id"],
                                   incident["source_ref_origine"]["tour_n"])]
        reprise = injection_by_ref[(incident["source_ref_reprise"]["session_id"],
                                    incident["source_ref_reprise"]["tour_n"])]
        if origin_target == reprise_target:
            incident_blocks[origin_target].append([origin, reprise])
        else:
            incident_blocks[origin_target].append([origin])
            incident_blocks[reprise_target].append([reprise])
    public: list[dict] = []
    ref_map: dict[tuple[str, int], dict] = {}
    speaker_map = {
        "humain": "participant_1", "instance_eip": "participant_2",
        "instance_coherence": "participant_2", "instance_alpha": "participant_1",
        "instance_beta": "participant_2",
    }
    for session_offset, (public_session, real_blocks) in enumerate(source_blocks.items()):
        injections = incident_blocks[public_session]
        random.Random(SEED + 10 + session_offset).shuffle(injections)
        # Intercalage stable : les tours réels gardent strictement leur ordre.
        blocks: list[list[dict]] = []
        cursor = 0
        for real_index, real_block in enumerate(real_blocks):
            remaining_slots = len(real_blocks) - real_index + 1
            remaining_injections = len(injections) - cursor
            take = (remaining_injections + remaining_slots - 1) // remaining_slots
            blocks.extend(injections[cursor:cursor + take])
            cursor += take
            blocks.append(real_block)
        blocks.extend(injections[cursor:])
        turn_n = 0
        for block in blocks:
            for row in block:
                turn_n += 1
                public.append({"session_id": public_session, "tour_n": turn_n,
                               "locuteur": speaker_map[row["locuteur"]],
                               "texte": row["texte"]})
                if row["session_id"].startswith("s"):
                    ref_map[(row["session_id"], row["tour_n"])] = {
                        "session_id": public_session, "tour_n": turn_n}

    remapped = json.loads(json.dumps(incidents, ensure_ascii=False))
    for incident in remapped:
        for key in ("source_ref_origine", "source_ref_reprise"):
            old = incident[key]
            incident[key] = ref_map[(old["session_id"], old["tour_n"])]
    return public, remapped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="autoriser la régénération d'une vérité terrain existante")
    args = parser.parse_args()
    source_path = Path("corpus/source/corpus_source.json")
    if not source_path.exists() or not source_path.stat().st_size:
        raise SystemExit("Corpus source D1 absent ou vide; exécuter prepare_localcontext_source.py")
    source = json.loads(source_path.read_text(encoding="utf-8"))
    injected, incidents = build_injections()
    corpus_path = Path("corpus/source/corpus_test.json")
    truth_path = Path("corpus/ground_truth/ground_truth.json")
    if truth_path.exists() and truth_path.stat().st_size and not args.force:
        raise SystemExit("Vérité terrain existante : utiliser --force pour une régénération explicite")
    corpus, incidents = compose_public_corpus(source, injected, incidents)
    corpus_path.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    truth_path.write_text(
        json.dumps({"seed": SEED, "incidents": incidents}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(incident["type"] for incident in incidents)
    print(f"[OK] corpus: {len(source)} tours réels anonymisés + {len(injected)} tours injectés")
    print(f"[OK] vérité terrain: {len(incidents)} incidents, {dict(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
