# Banc d'essai ETAU/SECS — Protocole multi-sprints pour exécution agentique

*Document destiné à un agent de code (Claude Code). Le cadrage, l'architecture et les critères d'acceptation sont fixés ici — l'agent n'a pas à interpréter l'objectif. L'agent code, exécute, loggue. Il ne juge pas les résultats : voir §5 sur la séparation des rôles.*

---

## 0. Cadrage

Ce protocole ne cherche pas à démontrer la supériorité d'ETAU/SECS sur une alternative. Il répond à deux questions, avec une règle de décision fixée avant tout résultat — pas après.

**Question 1** : à isolation égale entre instances, la structure propre à ETAU/SECS (schéma de sortie contraint, confiance graduée, arbitrage par cohérence plutôt que par vote, traçabilité obligatoire) détecte-t-elle et localise-t-elle davantage d'erreurs réelles qu'un simple vote majoritaire sur les mêmes instances isolées — et à quel coût supplémentaire ?

**Question 2**, orthogonale : l'isolation elle-même compte-t-elle ? On compare des instances qui ne se voient jamais (vote majoritaire, ETAU/SECS) à des instances qui se voient et révisent leur réponse au fil de rounds successifs.

**Règle de pivot (fixée maintenant, non négociable après coup)**
- Si le vote majoritaire égale ou dépasse ETAU/SECS en détection et localisation, à coût inférieur → le vote majoritaire devient la méthode par défaut ; ETAU/SECS devient une option pour les cas où la traçabilité a de la valeur indépendamment de la détection.
- Si la version allégée d'ETAU/SECS égale la version complète → la granularité fine de confiance est un raffinement non prioritaire, pas un invariant à défendre.
- Un résultat où une architecture gagne en détection mais perd en coût n'est pas tranché de force. Les deux chiffres sont rapportés tels quels.

**Ce que ce protocole n'est pas** : un test d'ETAU/SECS en conditions réelles sur un corpus de production. C'est un banc d'essai contrôlé, avec vérité terrain injectée et connue à l'avance — condition nécessaire pour que "détection" et "précision" signifient quelque chose. Un test sur corpus réel sans vérité terrain ne mesure que du volume de signal, jamais son exactitude.

---

## 1. Cinq architectures, pas deux

Le test ne compare pas "ETAU/SECS vs une alternative". Il croise deux axes indépendants, pour isoler ce qui produit réellement un effet :

| | Isolation stricte (aucune instance ne voit la sortie d'une autre avant sa propre clôture) | Contact autorisé (les instances se voient et révisent) |
|---|---|---|
| **Sortie libre, arbitrage par comptage** | **P1** — vote majoritaire | **P2** — débat multi-instances |
| **Schéma contraint, arbitrage par cohérence, traçabilité obligatoire** | **P3 / P4** — ETAU/SECS (allégé / complet) | *(non testé — combinaison défendue par aucune des deux méthodologies)* |

**P0** est hors tableau : une seule instance, aucun ensemble, sert de plancher de référence.

Un seul modèle, identique pour les cinq architectures, sur l'ensemble de l'expérience. C'est une contrainte non négociable : tout écart de résultat doit être attribuable à l'architecture, jamais à un facteur confondant de modèle.

### 1bis. Un biais de mesure à corriger avant d'écrire une ligne de code

Le score final (Recall, Précision — §4) dépend d'une mise en correspondance entre ce qu'une architecture rapporte et la vérité terrain. Si seules P3/P4 sont contraintes de citer une source exacte (session_id, tour_n) et que P0/P1/P2 rapportent en texte libre, le matching pour P0/P1/P2 devient approximatif (nécessite un appariement sémantique bruité), pendant que P3/P4 bénéficient d'un matching exact. Le résultat serait alors biaisé en faveur d'ETAU/SECS par construction du protocole, pas par mérite de la méthode.

**Correction imposée à toutes les architectures, y compris P0/P1/P2** : chaque assertion produite par n'importe quelle pipeline doit inclure un champ `source_ref` obligatoire (`session_id`, `tour_n`). Ce champ est syntaxique — il ne demande à aucune instance de raisonner sur la fiabilité de sa source, juste de citer où elle a lu ce qu'elle rapporte. Toutes les architectures peuvent le produire sans effort supplémentaire notable.

Cette correction déplace le vrai test de traçabilité : ce n'est plus "qui cite une source" (égal partout désormais) mais "la source citée permet-elle réellement de retrouver et vérifier l'assertion sans ambiguïté, et le chemin de preuve remonte-t-il jusqu'à l'origine" — c'est exactement M06 (§4), pas M01-M03.

---

## 2. Les cinq architectures — algorithme exact

Constantes partagées : N = 3 instances par ensemble, R = 2 rounds pour le débat, M = 2 instances de second niveau pour P4. Valeurs modifiables mais fixées identiques pour toute la durée d'un cycle de test — ne pas ajuster N en cours de route.

### P0 — Passe unique (plancher)
Une instance, un appel, contexte vierge, corpus entier en entrée. Produit une liste libre d'assertions avec `source_ref`. Aucun ensemble, aucune confiance déclarée. Sert à mesurer ce qu'apporte le simple fait d'avoir plusieurs instances, avant même de discuter d'architecture.

### P2 — Vote majoritaire (le baseline qui doit être pris au sérieux)
N instances, isolation stricte identique à P3/P4 — **l'isolation n'est pas la variable testée ici, seule la structure de sortie l'est**. Chaque instance reçoit un contexte frais (voir §2bis), le corpus entier, un prompt d'extraction fixe identique pour les trois, et produit une liste libre d'assertions avec `source_ref`. Agrégation **par code, pas par une instance IA** : deux assertions dont le `source_ref` coïncide et dont le texte dépasse un seuil de similarité sémantique (embedding cosine, seuil à fixer en Sprint 1) sont regroupées. Une assertion portée par ≥2/3 instances est retenue sans label de confiance particulier — juste "retenue" ou "rejetée" sur seuil de comptage. C'est le comptage brut, sans jugement de cohérence.

### P1 — Débat multi-instances (le baseline qui autorise le contact)
N instances. Round 1 : identique à P2, chaque instance produit sa liste isolément. Round 2 à R : chaque instance reçoit sa propre sortie du round précédent **et** les sorties anonymisées des autres instances, avec instruction de réviser, confirmer ou retirer chaque assertion à la lumière de ce qu'ont vu les autres. Après le round R, agrégation par le **même code d'agrégation que P2** (comptage, seuil identique) sur les sorties du dernier round — pour que la seule variable entre P1 et P2 soit la présence ou l'absence de contact inter-instances, pas la méthode d'agrégation finale.

Ce baseline existe parce que la littérature sur le débat multi-agents montre un risque documenté : le consensus qui émerge d'un débat peut converger vers la réponse la plus confiante plutôt que la plus correcte, particulièrement quand les instances partagent les mêmes biais de départ. Un résultat où P1 sous-performe P2 malgré (ou à cause) du contact serait un résultat attendu par cette littérature, pas une anomalie du protocole.

### P3 — ETAU/SECS allégé
N parseurs isolés (identique à P2 côté isolation), schéma contraint (`source_ref` obligatoire, pas de champ de confiance individuel — voir ci-dessous), puis **un arbitre unique** qui reçoit uniquement les N sorties structurées des parseurs, jamais le corpus brut. L'arbitre applique une règle de cohérence, pas un simple seuil de comptage : une assertion portée par 1/N mais assortie d'un raisonnement autonome vérifiable dans le `source_ref` peut être retenue avec un label `FORT`, tandis qu'une assertion portée par 2/N sans justification distincte au-delà de la ressemblance thématique peut rester `FAIBLE`. C'est ici, à l'arbitrage, que la confiance est assignée — jamais par un parseur sur sa propre sortie. Confiance binaire : `FORT` / `FAIBLE`. Traçabilité au niveau du fil (pas de la ligne individuelle).

### P4 — ETAU/SECS complet
Trois étages, fidèles à la spécification native : N parseurs isolés (round 1) → M cartographes isolés (round 2, ne reçoivent que les sorties structurées des parseurs, jamais le corpus brut) → un noyau de cohérence unique (round 3, ne reçoit que les sorties des cartographes). Confiance à trois niveaux : `FORT` (N/N), `PROBABLE` ((N-1)/N), `FAIBLE` (1/N porté par argument autonome). Traçabilité choisie à l'option B (niveau du fil, produite en round 2) — voir §6, décision D3.

**Adaptation nécessaire pour ce protocole, à documenter explicitement dans le rapport final** : en usage courant, les N parseurs de passe 1 partitionnent un corpus volumineux (chacun lit une portion différente). Pour ce banc d'essai, les N parseurs lisent chacun l'**intégralité** du corpus de test — condition nécessaire pour calculer un score de convergence par assertion. Ce n'est pas une redéfinition de la méthode, c'est un choix d'instrumentation pour la rendre mesurable ; à signaler comme tel dans `ANALYSIS_PROTOCOL.md` (§7).

### 2bis. Isolation réelle — contrainte d'implémentation, pas de formulation de prompt

L'isolation ne se simule pas en demandant à un modèle de "faire semblant" d'être une instance isolée dans un même fil de conversation — le contexte partagé contamine silencieusement, même sans mention explicite des autres instances. L'isolation s'impose par le code : chaque appel isolé construit une liste `messages` fraîche, à un seul élément, sans historique de conversation antérieur.

```python
def isolated_call(client, model, prompt_fixe, corpus_text):
    messages = [{"role": "user", "content": f"{prompt_fixe}\n\n---\n{corpus_text}"}]
    assert len(messages) == 1, "violation d'isolation : contexte multi-tours détecté"
    return client.messages.create(model=model, max_tokens=2000, messages=messages)
```

Contrainte symétrique pour les arbitres/cartographes/noyau : leur fonction ne doit **pas avoir accès en paramètre** au texte du corpus brut — pas "instruction de ne pas s'en servir", mais absence structurelle du paramètre dans la signature de la fonction, vérifiable par lecture de code.

```python
def arbitrer(client, model, prompt_arbitrage, sorties_structurees_passe_precedente):
    # aucun paramètre corpus_text ici — impossible d'y accéder même par erreur
    ...
```

Pour P1 (débat), c'est l'inverse qui doit être vérifié explicitement : un test doit confirmer que les sorties des autres instances sont bien présentes dans le contexte du round suivant — sinon P1 dégénère silencieusement en P2 répété N fois, et toute la comparaison entre les deux devient invalide sans que rien ne le signale.

---

## 3. Corpus et vérité terrain

### Nature du corpus
Un corpus réel existant, au format `{session_id, tour_n, locuteur, texte}`, suffisamment court pour tenir dans un seul appel par instance (condition de §2 pour P2-P4). Le choix du corpus source est une décision bloquante — voir D1 en §6.

### Taxonomie des incidents injectés
Six types, injectés à des positions connues **avant** toute exécution de pipeline, dans un fichier `ground_truth.json` immuable une fois créé :

| Type | Ce qui est injecté | Comportement correct attendu |
|---|---|---|
| `CONTRADICTION_INTRA` | Un même locuteur affirme deux choses incompatibles dans la même session | Détecté par une seule instance déjà, sans comparaison inter-instances |
| `CONTRADICTION_INTER` | Deux sessions distinctes affirment des faits incompatibles sur le même objet | Ne peut être détecté qu'au niveau de l'arbitrage/cartographie, jamais par un parseur isolé |
| `DERIVE` | Une affirmation hédée ("il semble que...") est reprise plus tard comme fait établi, sans nouvelle preuve | Test direct de la dérive épistémique documentée par ailleurs |
| `NON_ETAYE` | Une affirmation à haute confiance apparente, sans aucune source traçable dans le corpus | Test de la capacité à signaler l'absence de fondement, pas juste la présence de contenu |
| `LACUNE_SILENCIEUSE` | Un sujet soulevé comme important en début de corpus n'est jamais résolu, mais une session ultérieure agit comme s'il l'avait été | Analogue textuel d'un silence porteur de signal — la bonne réponse est de signaler l'absence de résolution, pas de la combler |
| `AMBIGU_GENUINE` | Deux lectures légitimes et non tranchables coexistent dans le corpus, sans qu'aucune ne soit fausse | La bonne réponse est l'absence de clôture, rapportée explicitement — une architecture qui force une résolution ici échoue le test même si sa réponse "semble" raisonnable |

Minimum 4 incidents par type, soit 24 au total, pour que les métriques de §4 aient un sens statistique en dessous du bruit d'échantillonnage.

### `generate_corpus.py` — étape 0, avant tout le reste
Lit le corpus source, injecte les incidents aux positions choisies, écrit deux artefacts **avant qu'aucune pipeline ne s'exécute** :
- le corpus modifié (celui que les pipelines liront)
- `ground_truth.json`, qui n'est jamais passé en paramètre à aucune pipeline — seulement à `metrics.py` (§4), après coup

```json
{
  "incidents": [
    {
      "incident_id": "INC-07",
      "type": "DERIVE",
      "source_ref_origine": {"session_id": "sess-02", "tour_n": 14},
      "source_ref_reprise": {"session_id": "sess-05", "tour_n": 3},
      "description_courte": "hypothèse non vérifiée en s02t14, réaffirmée comme fait en s05t03 sans nouvelle preuve"
    }
  ]
}
```

---

## 4. Métriques

| # | Métrique | Mesure | Ce qui est testé |
|---|---|---|---|
| M01 | Detection Recall | incidents détectés / incidents injectés | La question 1 centrale |
| M02 | Localization Precision | détections dont le `source_ref` correspond exactement à l'incident réel / détections totales | Distingue "a vu qu'il y avait un problème" de "sait où" |
| M03 | False Signal Rate | signaux rapportés ne correspondant à aucun incident injecté / signaux totaux | Le coût caché d'une détection agressive |
| M04 | Confidence Calibration | taux d'exactitude parmi les assertions `FORT` vs parmi les `FAIBLE` (P3/P4 seulement) | La confiance déclarée est-elle informative ou décorative |
| M05 | Cost per Detection | (tokens + temps) / vrais positifs | Le prix réel de chaque architecture, pas seulement sa performance brute |
| M06 | Traceability Utility | test aveugle **manuel**, hors agent de code : un testeur humain reçoit 8 assertions tirées au sort dans les sorties finales et chronomètre le temps pour retrouver la source exacte dans le corpus sans aide | Le vrai différenciateur de traçabilité, séparé de M01-M03 (§1bis) |
| M07 | Clôture appropriée | sur les incidents `AMBIGU_GENUINE` uniquement : % d'architectures qui rapportent une non-résolution plutôt qu'une fausse clôture | Teste directement l'axiome de clôture stricte, pas la détection en général |
| M08 | Implementation Effort | lignes de code par pipeline, nombre d'appels LLM par cycle complet | Faisabilité d'adoption — la question posée dès le départ : ce protocole fait-il gagner du temps ou en perdre |

M06 et M07 ne sont pas automatisables par l'agent de code seul. M06 requiert un humain ; M07 requiert que le testeur humain confirme manuellement, sur l'échantillon `AMBIGU_GENUINE`, que la lecture du corpus est réellement indécidable et pas juste mal rédigée — sinon la métrique mesure la qualité de la rédaction du corpus, pas la méthode.

---

## 5. Rôles — non-contamination du dispositif de test lui-même

Le dispositif expérimental est soumis à la même règle qu'il teste : celui qui code les pipelines ne doit pas être celui qui juge les résultats.

- **Agent de code (Claude Code, ce document)** : construit les cinq pipelines, exécute, produit `results/`. Ne reçoit jamais `ground_truth.json` en entrée d'aucune pipeline — seulement `metrics.py` y accède, en aval, une fois les sorties déjà figées.
- **Instance d'analyse, contexte séparé, jamais exposée au code ni aux prompts d'exécution** : reçoit uniquement le contenu de `results/`, produit l'interprétation. Si la même instance a écrit le code des pipelines ET analyse leurs résultats, l'analyse est structurellement suspecte — pas par malveillance, par la même logique qui interdit à un parseur isolé de s'auto-arbitrer.
- **Arbitre final : l'auteur des méthodes.** Décide de l'application de la règle de pivot (§0). Aucune instance IA ne décide du pivot à sa place.

---

## 6. Décisions bloquantes avant Sprint 0

Rien en Sprint 0 ne peut commencer sans ces quatre réponses.

- **D1 — Corpus source.** Quel corpus réel sert de base ? S'il contient des données client ou institutionnelles sensibles, doit-il être anonymisé avant injection (noms de locuteurs, identifiants d'organisation) ? Un corpus destiné à un dépôt versionné, même privé, mérite cette question posée une fois plutôt que découverte après coup.
- **D2 — Modèle et budget.** Un seul modèle pour les cinq architectures (§1, contrainte non négociable). Lequel ? Budget approximatif attendu : ~23 appels LLM par cycle complet sur le corpus (1 pour P0, 6 pour P1, 6 pour P2, 4 pour P3, 6 pour P4). Avec 5 cycles répétés pour absorber la variance de température, ~115 appels au total — raisonnable, mais à confirmer avant de lancer.
- **D3 — Traçabilité de P4.** L'option B (niveau du fil, produite en round 2) est prise par défaut ici, uniquement pour permettre l'exécution de ce test. Ceci **ne tranche pas** la question de traçabilité ligne-à-ligne restée ouverte par ailleurs dans la spécification de la méthode — ce document choisit une valeur provisoire testable, pas une résolution définitive.
- **D4 — Seuil de similarité sémantique** pour l'agrégation par code de P1/P2 (§2). Une valeur par défaut sera proposée en Sprint 1 à partir d'un échantillon manuel, mais elle doit être validée avant d'être figée pour tout le cycle.

---

## 7. Plan multi-sprints

### Sprint 0 — Fondations
Squelette de dépôt (§8), `requirements.txt`, `generate_corpus.py`, `ground_truth.json`.
**Critère d'acceptation** : `ground_truth.json` existe, contient ≥24 incidents répartis sur les 6 types (≥4 chacun), est généré avec une graine aléatoire fixée et documentée (reproductibilité), et n'est référencé par aucun script de pipeline — seulement par `metrics.py`.

### Sprint 1 — P0 et P1 (baselines sans structure)
`pipeline_p0.py`, `pipeline_p1.py`, `common/isolation.py`, `common/agregation.py` (le module de comptage partagé entre P1 et P2).
**Critère d'acceptation** : un test automatisé confirme qu'aucun appel isolé ne reçoit plus d'un message dans son historique (assertion de §2bis exécutée, pas seulement documentée) ; le seuil de similarité D4 est fixé et justifié dans un court rapport.

### Sprint 2 — P2 (débat, contact autorisé)
`pipeline_p2.py`, logs conservés **par round**, pas seulement la sortie finale.
**Critère d'acceptation** : un test automatisé confirme que le contexte du round 2 contient bien littéralement les sorties du round 1 des autres instances (pas seulement de la sienne) — la vérification inverse de celle du Sprint 1.

### Sprint 3 — P3 et P4 (ETAU/SECS)
`pipeline_p3.py`, `pipeline_p4.py`. Implémente D3.
**Critère d'acceptation** : lecture de code confirme que les fonctions d'arbitrage/cartographie n'ont structurellement aucun paramètre `corpus_text` dans leur signature (§2bis) ; le label de confiance n'apparaît que dans la sortie finale de l'arbitre/noyau, jamais dans les sorties individuelles des parseurs.

### Sprint 4 — Métriques
`metrics.py` calcule M01-M05, M08 pour les cinq pipelines sur les 24+ incidents. Produit `metrics_report.json` et `summary.csv`.
**Critère d'acceptation** : `summary.csv` lisible directement par l'instance d'analyse (§5) sans traitement supplémentaire ; M06 et M07 apparaissent dans le rapport comme `"required_manual_step": true`, pas comme des champs vides silencieux — l'absence d'automatisation doit être visible, pas masquée.

### Sprint 5 — Clôture et passation
`ANALYSIS_PROTOCOL.md` documentant : l'adaptation de P4 signalée en §2 (parseurs redondants plutôt que partition), les valeurs finales de D1-D4, tout écart entre ce document et ce qui a réellement été codé. `PROGRESSION.md` mis à jour. Dossier `results/` transmis à l'instance d'analyse séparée (§5), jamais à l'agent qui a écrit le code.
**Critère d'acceptation** : quelqu'un qui n'a lu que `results/` et ce document peut reproduire la logique de scoring sans consulter le code source.

---

## 8. Structure du dépôt

```
banc-essai/
├── README.md
├── requirements.txt
├── CHANGELOG.md
├── PROGRESSION.md
├── corpus/
│   ├── source/
│   ├── generate_corpus.py
│   └── ground_truth.json
├── pipelines/
│   ├── common/
│   │   ├── isolation.py
│   │   └── agregation.py
│   ├── pipeline_p0.py
│   ├── pipeline_p1.py
│   ├── pipeline_p2.py
│   ├── pipeline_p3.py
│   └── pipeline_p4.py
├── metrics/
│   └── metrics.py
├── run_experiment.py
└── results/
    └── cycle_<n>/
        ├── raw_outputs/
        ├── metrics_report.json
        ├── summary.csv
        └── ANALYSIS_PROTOCOL.md
```

**Contraintes de livraison** : exécution en une seule commande (`python run_experiment.py --cycles 5`), aucun input interactif, chaque pipeline dans son propre fichier, chaque décision de formule non triviale commentée dans le code — en particulier la formule de similarité sémantique (D4) et la règle de cohérence de l'arbitre P3/P4, qui ne sont pas de simples seuils et méritent d'être justifiées en ligne.

---

## 9. Ce que ce protocole ne teste pas

Il ne teste pas ETAU/SECS sur un corpus volumineux avec partition réelle (§2, adaptation P4). Il ne teste pas la robustesse à un changement de modèle (D2 fixe un seul modèle par construction — un résultat favorable ici pourrait être un artefact de ce modèle précis, pas une propriété générale de l'architecture). Il ne teste pas le coût humain de supervision du protocole lui-même, seulement le coût machine (M08 ne compte pas le temps de l'arbitre final humain). Il ne mesure pas si les erreurs détectées auraient été trouvées de toute façon par une relecture humaine ordinaire — ce protocole compare des architectures IA entre elles, pas une architecture IA à un statu quo humain.

---

## 10. Questions ouvertes, non bloquantes pour Sprint 0

- Une fois un premier cycle exécuté, faut-il faire varier N (3 → 5) comme second facteur expérimental, ou est-ce prématuré avant d'avoir un premier résultat sur N=3 ?
- Le choix de l'option B pour D3 (§6) reste provisoire. Si le résultat de Sprint 3-4 montre que P4 ne dépasse pas P3 de façon notable, la question de trancher entre les options A/B/C ailleurs perd une partie de son urgence — un résultat négatif ici est aussi une réponse utile à cette question distincte.
- Faut-il répéter le cycle complet avec un second modèle une fois qu'un premier résultat existe sur le modèle choisi en D2, pour vérifier que le résultat n'est pas un artefact du modèle ? Non prioritaire avant un premier passage complet, mais à budgétiser si le premier cycle est concluant.

---

*Document v0.1 — première formalisation, aucune version antérieure. Statut : prêt pour Sprint 0 sous réserve des décisions D1-D4 (§6). Document autonome pour exécution agentique — ne suppose aucun contexte de conversation antérieur.*
