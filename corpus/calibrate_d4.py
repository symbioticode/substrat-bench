#!/usr/bin/env python3
"""Calibre D4 sur 50 paires étiquetées et validées, sans fallback lexical."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
POSITIVE_PAIRS = [
    ("durée du pilote de six semaines", "le test pilote est prévu pour six semaines"),
    ("durée du pilote de douze semaines", "le test s'étendra sur douze semaines"),
    ("aucune donnée personnelle conservée", "aucune information nominative ne sera gardée"),
    ("adresses nominatives gardées un an", "conservation annuelle des adresses personnelles"),
    ("rapport envoyé mensuellement", "fréquence mensuelle d'envoi du rapport"),
    ("rapport transmis chaque semaine", "livraison hebdomadaire du rapport"),
    ("aucune décision prise par le système", "le système ne décide jamais de façon autonome"),
    ("priorisation automatique des actions", "le système choisit seul les actions prioritaires"),
    ("budget maximal de deux mille unités", "plafond budgétaire fixé à 2 000 unités"),
    ("source mise à jour chaque jour", "actualisation quotidienne de la source"),
    ("consentement requis avant collecte", "la collecte exige un accord préalable explicite"),
    ("déploiement limité aux commerces physiques", "seuls les points de vente physiques sont ciblés"),
    ("démarrage possible en septembre", "le pilote pourrait commencer au mois de septembre"),
    ("taux de réponse provisoire de vingt pour cent", "hypothèse temporaire d'un taux de réponse à 20 %"),
    ("conformité juridique non vérifiée", "la validation légale reste encore à effectuer"),
    ("réduction possible de la charge administrative", "le modèle pourrait alléger les tâches administratives"),
    ("baisse des coûts annoncée sans preuve", "aucune mesure ne justifie la réduction de coûts promise"),
    ("préférence utilisateur sans enquête", "aucune étude ne soutient la préférence attribuée aux utilisateurs"),
    ("doublement du marché non sourcé", "la croissance du marché est annoncée sans projection vérifiable"),
    ("suppression totale des erreurs non démontrée", "aucun test ne prouve que toutes les erreurs disparaissent"),
    ("responsabilité en cas de perte non résolue", "la question du responsable d'un dommage reste ouverte"),
    ("détection des sources obsolètes non définie", "aucune réponse sur le repérage d'une source périmée"),
    ("plan de retour arrière absent", "aucune procédure de repli n'est fournie"),
    ("client peut désigner entreprise ou représentant", "deux sens possibles du mot client restent valides"),
    ("réussite mesurée par argent ou temps", "gain financier et temps libéré sont deux critères possibles")]


def labelled_pairs() -> list[dict]:
    positives = [{"left": left, "right": right, "same": True} for left, right in POSITIVE_PAIRS]
    negatives = [{"left": left, "right": POSITIVE_PAIRS[(index + 9) % len(POSITIVE_PAIRS)][1], "same": False}
                 for index, (left, _) in enumerate(POSITIVE_PAIRS)]
    return positives + negatives


def main() -> int:
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit("sentence-transformers requis; fallback lexical interdit pour D4") from exc
    pairs = labelled_pairs()
    payload = json.dumps(pairs, ensure_ascii=False, sort_keys=True).encode()
    model = SentenceTransformer(MODEL)
    texts = [text for pair in pairs for text in (pair["left"], pair["right"])]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    similarities = [float(embeddings[2*i] @ embeddings[2*i+1]) for i in range(len(pairs))]
    candidates = []
    for threshold_step in range(20, 91):
        threshold = threshold_step / 100
        tp = sum(pair["same"] and score >= threshold for pair, score in zip(pairs, similarities))
        fp = sum(not pair["same"] and score >= threshold for pair, score in zip(pairs, similarities))
        fn = sum(pair["same"] and score < threshold for pair, score in zip(pairs, similarities))
        tn = len(pairs) - tp - fp - fn
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        candidates.append({"threshold": threshold, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
                           "precision": precision, "recall": recall, "f1": f1})
    best = max(candidates, key=lambda row: (row["f1"], row["precision"], row["threshold"]))
    report = {"model": MODEL, "pairs": len(pairs), "positive": 25, "negative": 25,
              "dataset_sha256": hashlib.sha256(payload).hexdigest(), "selection": "max F1; tie precision puis seuil",
              "best": best, "observations": [{**pair, "similarity": score}
                                                for pair, score in zip(pairs, similarities)]}
    output = Path("corpus/d4_calibration_report.json")
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(best, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
