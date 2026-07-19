# CLAUDE.md — Instructions pour Claude Code Web (banc-essai ETAU/SECS)

## Identité du projet
Banc d'essai contrôlé ETAU/SECS — validation expérimentale multi-sprints.
Repo : banc-essai/
Branche principale : main

## Convention de nommage
- **ETAU** : Épistemic Traceability & Auditability Unit
- **SECS** : Sequential Epistemic Consistency Scoring
- Pipelines : P0, P1, P2, P3, P4 (selon §1 doc protocole)
- Métriques : M01–M08 (selon §4 doc protocole)
- Décisions bloquantes : D1–D4 (selon §6 doc protocole)

## Règles opérationnelles (héritées de EIP)

| ID | Règle |
|----|-------|
| R-DOC-01 | Maximum 4 fichiers documentation core dans le repo (README.md, CHANGELOG.md, STATUS.md, VARIABLES.md) |
| R-DEC-01 | Toute décision d'architecture tracée dans `brainstorm/BR-XXX.md` |
| R-QO-01 | Toute question non résolue tracée avec identifiant `QO-Sn-XX` |
| R-ISO-01 | **Isolation réelle** : chaque appel LLM isolé = `messages=[{role:user}]` seul, sans historique (§2bis) |
| R-ISO-02 | Arbitres/cartographes n'ont **jamais** `corpus_text` en paramètre (§2bis) |
| R-ISO-03 | P1 (débat) : test automatisé confirme injection sorties round N-1 dans round N |
| R-GT-01 | `ground_truth.json` **jamais** passé aux pipelines — seulement à `metrics.py` en aval |
| R-REPRO-01 | Seed global fixé, dépendances versionnées, résultats bit-à-bit identiques |
| R-STAT-01 | Comparaisons : test statistique + barres d'erreur (IQR sur 5 runs minimum) |
| R-PIVOT-01 | Règle de pivot (§0) fixée **avant** tout résultat — non négociable après coup |
| R-ROLE-01 | Agent code ≠ Instance analyse ≠ Arbitre final (toi) — séparation structurelle (§5) |

## Source de vérité
Le repo GitHub est la source de vérité. La conversation est éphémère.
Toute session commence par : `git pull`
Toute session se termine par : commit de `STATUS.md` à jour.

## Format des commits
`[SPRINT-N] action courte : fichier(s) modifié(s)`
Exemple : `[SPRINT-1] add isolation module with assertions : pipelines/common/isolation.py`

## Matrice des modèles (adaptée de EIP §3.2)

| Tâche | Modèle recommandé | Justification |
|-------|-------------------|---------------|
| Décisions architecturales BR, analyse théorique | **Opus 4.7 + extended thinking** | Raisonnement multi-étapes, rigueur |
| **L'Analyste (REV-Sx.md)** | **Opus 4.7 + extended thinking + instance isolée** | Regard externe simulé, slow reasoning forcé |
| Implémentation code Python, exécution pipelines | **Jules (Google) ou Sonnet** | Qualité exécution, économise tokens Opus |
| Corrections post-REV, reformulations | **Sonnet** | Tâche exécution, pas invention |
| Comptage, GNG, stats, vérifications | **Haiku** | Tâches structurées répétables, coût minimal |

> **Note** : Pour ce banc d'essai, les appels LLM réels (D2) nécessitent clés API. Le code est écrit pour être agnostique (interface `LLMClient`).

## Architecture d'isolation (cœur du protocole §2bis)

```python
# pipelines/common/isolation.py — PATTERN OBLIGATOIRE
def isolated_call(client, model, prompt_fixe, corpus_text):
    messages = [{"role": "user", "content": f"{prompt_fixe}\n\n---\n{corpus_text}"}]
    assert len(messages) == 1, "violation isolation : contexte multi-tours détecté"
    return client.messages.create(model=model, max_tokens=2000, messages=messages)

# Arbitre / Cartographe / Noyau — PAS de corpus_text en paramètre
def arbitrer(client, model, prompt_arbitrage, sorties_structurees_passe_precedente):
    # aucun paramètre corpus_text ici — impossible d'y accéder même par erreur
    ...
```

## Rôles — non-contamination (§5)

| Rôle | Responsabilité | Accès `ground_truth.json` |
|------|----------------|---------------------------|
| **Agent de code (ce document)** | Construit les 5 pipelines, exécute, produit `results/` | **JAMAIS** — seulement `metrics.py` y accède en aval |
| **Instance d'analyse (contexte séparé)** | Reçoit `results/`, produit interprétation | **JAMAIS** — ne voit que sorties pipelines |
| **Arbitre final (toi)** | Décide application règle de pivot (§0) | Seul à connaître la vérité terrain |

---

## Sprint 0 — Checklist de démarrage (adaptée EIP Annexe A)

```
  — Fondations repo —
□ VARIABLES.md complété (blocs 1–8)
□ Repo GitHub créé avec branch principale (main)
□ CLAUDE.md au format Claude Code Web
□ STATUS.md initialisé (Sprint courant = 0, statut = PRÊT, VERSION = v0.1)
□ Arborescence créée via init_project.sh
□ README.md squelette commité
□ requirements.txt créé : Python 3.11+, PyTorch 2.x, transformers, sentence-transformers, scikit-learn, crowdkit, openai, anthropic, tenacity, tqdm, rich, pyyaml, pytest

  — Vérifications techniques —
□ Modèle unique D2 choisi et clés API disponibles
□ SentenceTransformer (pour similarité D4) téléchargeable
□ Crowd-Kit (Dawid-Skene) installable : `pip install crowdkit`
□ Connectivity agent code (Jules/Sonnet) ↔ GitHub testée

  — Décisions bloquantes D1–D4 (§6) —
□ D1 — Corpus source choisi, anonymisation décidée
□ D2 — Modèle unique + budget validé
□ D3 — Traçabilité P4 (Option B par défaut) confirmée
□ D4 — Seuil similarité sémantique validé (échantillon manuel Sprint 1)

  — Décisions architecturales pré-tracées (BR) —
□ BR-001 à BR-010 créés avec statut PROPOSÉ
□ LLM Council lancé sur BR critiques si requis
```