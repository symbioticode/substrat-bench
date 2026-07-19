# Banc d'essai ETAU/SECS — Protocole multi-sprints pour exécution agentique (v0.2)

*Document destiné à un agent de code (Claude Code). Le cadrage, l'architecture et les critères d'acceptation sont fixés ici — l'agent n'a pas à interpréter l'objectif. L'agent code, exécute, loggue. Il ne juge pas les résultats : voir §5 sur la séparation des rôles.*

---

## 0. Changelog v0.1 → v0.2

Cette révision importe la mécanique de gouvernance de `methodologie-agentique-EIP-v3.1.md` — pas son contenu de domaine (théorème, canaux, ICLR). Ce qui est repris est le squelette opérationnel : source de vérité = dépôt, sprints atomiques, instance d'analyse isolée, règles numérotées invocables par référence, score Go/No-Go calculé en cours de route, décisions tracées individuellement. Ce qui n'est pas repris : rien du domaine EIP lui-même n'apparaît ci-dessous.

1. **Environnement NixOS natif ajouté** (§8bis, nouveau) — `shell.nix`, garde-fous `.gitignore`, journal d'incidents. Remplace la mention générique de `requirements.txt` seul en v0.1.
2. **Découpage en fichiers de contexte par sprint** (§7, note liminaire) — chaque sprint devient un fichier autonome `sprints/SPRINT-N-context.md` avec discipline « à lire / à ne pas lire », plutôt qu'un unique document relu en entier à chaque session.
3. **Décisions D1-D4 reformalisées au format BR** (§6, restructuré) — statut, décideur, date, options, tracées individuellement comme dans `brainstorm/BR-XXX.md` plutôt qu'en liste plate.
4. **Quatre personas adversariaux ajoutés** (§5bis, nouveau) — attaquent chaque livrable de sprint avant la passation à l'instance d'analyse (§5). Rôle repris de la méthodologie source, personas reconstruits pour le domaine de la vérification épistémique plutôt que la relecture de papier.
5. **Porte LLM Council ajoutée sur BR-003** (§6) — seule décision du lot qui remplit le critère à trois conditions de la règle source (décision d'architecture + deux options défendables + erreur coûteuse après le sprint suivant).
6. **Grille de score SCORE-BE ajoutée** (§7bis, nouveau) — remplace le critère d'acceptation en une ligne par sprint par une évaluation à cinq dimensions, calculée à partir de Sprint 4.
7. **Règles numérotées introduites** (§0bis, nouveau) — des contraintes déjà présentes en prose en v0.1 deviennent invocables par référence (`R-ISOL-01`, etc.).
8. **Confidentialité de la taxonomie imposée** (§3bis, nouveau) — la liste des six types d'incidents ne doit jamais atteindre les instances d'extraction, seulement `metrics.py`. Absente de v0.1, où cette fuite n'était pas explicitement bloquée : une pipeline qui saurait à l'avance qu'elle cherche exactement six catégories connues ne serait plus testée sur sa capacité de détection, mais sur sa capacité à cocher une grille.
9. **Deux erreurs corrigées, trouvées en relisant v0.1 pour cette révision** :
   - le tableau de §1 et les en-têtes de §2 assignaient P1/P2 de façon inversée entre vote majoritaire et débat. Corrigé et vérifié dans tout le document.
   - le budget d'appels LLM (ancien §6, D2) comptait 6 appels pour le vote majoritaire (P1) alors que l'algorithme décrit n'en utilise que 3 (pas de rounds de révision). Total corrigé : 20 appels par cycle, pas 23 ; ~100 sur 5 cycles, pas ~115.
10. **BR-004 (ex-D4) révisée** : la mise en correspondance des assertions de P1/P2 par similarité d'embedding est remplacée, en option recommandée, par un appel-juge à un modèle économique — évite d'ajouter une dépendance ML locale lourde (`sentence-transformers`, `torch`) à un environnement NixOS qui n'en a par ailleurs aucun besoin.

---

## 0bis. Règles numérotées

Convention reprise de `methodologie-agentique-EIP-v3.1.md` : `CLAUDE.md` du dépôt cite ces règles par identifiant, sans les reformuler à chaque section.

| ID | Règle |
|---|---|
| R-ISOL-01 | Toute pipeline déclarée isolée (P0, P1, P3, P4) passe un test automatisé confirmant qu'aucun appel isolé ne reçoit plus d'un message dans son historique. Une isolation non vérifiée par le code n'est pas une isolation, c'est une déclaration. |
| R-ISOL-02 | Toute fonction d'arbitrage, de cartographie ou de noyau ne peut recevoir le corpus brut en paramètre — vérifiable par lecture de signature, pas par instruction de prompt. |
| R-CONTACT-01 | P2 (débat) passe le test symétrique de R-ISOL-01 : le contexte du round N contient littéralement les sorties du round N-1 des autres instances. |
| R-MESURE-01 | Le champ `source_ref` est obligatoire dans la sortie de toutes les architectures P0-P4, sans exception (§1bis). |
| R-SECRET-01 | La taxonomie d'incidents (§3) et `ground_truth.json` ne sont communiqués à aucune instance d'extraction ou d'arbitrage — seulement à `metrics.py`, en aval (§3bis). |
| R-MODELE-01 | Un seul modèle pour les cinq architectures sur toute la durée d'un cycle. Tout changement de modèle en cours de cycle invalide le cycle entier. |
| R-PIVOT-01 | La règle de pivot (§0) ne peut être reformulée après l'obtention d'un premier résultat. Toute modification après Sprint 4 est tracée dans un BR distinct, justifiée sans référence au résultat obtenu. |
| R-BR-01 | Toute décision (corpus, modèle, traçabilité, mise en correspondance) est tracée en `brainstorm/BR-XXX.md` avant le sprint qui en dépend, jamais après. |
| R-SPRINT-01 | Un sprint ne démarre pas si le critère d'acceptation du précédent n'est pas satisfait, sauf dérogation tracée par l'arbitre final (§5). |
| R-SCORE-01 | La grille SCORE-BE (§7bis) est calculée à partir de Sprint 4 ; un score < 60 sur une dimension bloque le sprint suivant tant que la dimension n'est pas corrigée. |
| R-COUNCIL-01 | *(reprise verbatim de la méthodologie source)* Le LLM Council est invoqué si et seulement si : décision architecturale BR + deux options défendables + erreur coûteuse après le sprint suivant. |

---

## 1. Cinq architectures, pas deux

Le test ne compare pas « ETAU/SECS vs une alternative ». Il croise deux axes indépendants, pour isoler ce qui produit réellement un effet :

| | Isolation stricte (aucune instance ne voit la sortie d'une autre avant sa propre clôture) | Contact autorisé (les instances se voient et révisent) |
|---|---|---|
| **Sortie libre, arbitrage par comptage** | **P1** — vote majoritaire | **P2** — débat multi-instances |
| **Schéma contraint, arbitrage par cohérence, traçabilité obligatoire** | **P3 / P4** — ETAU/SECS (allégé / complet) | *(non testé — combinaison défendue par aucune des deux méthodologies)* |

**P0** est hors tableau : une seule instance, aucun ensemble, sert de plancher de référence.

Un seul modèle, identique pour les cinq architectures, sur l'ensemble de l'expérience (`R-MODELE-01`). C'est une contrainte non négociable : tout écart de résultat doit être attribuable à l'architecture, jamais à un facteur confondant de modèle.

### 1bis. Un biais de mesure à corriger avant d'écrire une ligne de code

Le score final (Recall, Précision — §4) dépend d'une mise en correspondance entre ce qu'une architecture rapporte et la vérité terrain. Si seules P3/P4 sont contraintes de citer une source exacte (session_id, tour_n) et que P0/P1/P2 rapportent en texte libre, le matching pour P0/P1/P2 devient approximatif, pendant que P3/P4 bénéficient d'un matching exact. Le résultat serait alors biaisé en faveur d'ETAU/SECS par construction du protocole, pas par mérite de la méthode.

**Correction imposée à toutes les architectures (`R-MESURE-01`)** : chaque assertion produite par n'importe quelle pipeline doit inclure un champ `source_ref` obligatoire (`session_id`, `tour_n`). Champ syntaxique — il ne demande à aucune instance de raisonner sur la fiabilité de sa source, juste de citer où elle a lu ce qu'elle rapporte.

Cette correction déplace le vrai test de traçabilité : ce n'est plus « qui cite une source » (égal partout désormais) mais « la source citée permet-elle réellement de retrouver et vérifier l'assertion sans ambiguïté » — c'est M06 (§4), pas M01-M03.

---

## 2. Les cinq architectures — algorithme exact

Constantes partagées : N = 3 instances par ensemble, R = 2 rounds pour le débat, M = 2 instances de second niveau pour P4. Valeurs modifiables mais fixées identiques pour toute la durée d'un cycle de test.

### P0 — Passe unique (plancher)
Une instance, un appel, contexte vierge, corpus entier en entrée. Produit une liste libre d'assertions avec `source_ref`. Aucun ensemble, aucune confiance déclarée.

### P1 — Vote majoritaire (le baseline qui doit être pris au sérieux)
N=3 instances, isolation stricte identique à P3/P4 — **l'isolation n'est pas la variable testée ici, seule la structure de sortie l'est**. Chaque instance reçoit un contexte frais (§2bis), le corpus entier, un prompt d'extraction fixe identique pour les trois, et produit une liste libre d'assertions avec `source_ref`. Agrégation **par code, pas par une instance IA** : deux assertions dont le `source_ref` coïncide et dont le texte est jugé équivalent (mise en correspondance, BR-004) sont regroupées. Une assertion portée par ≥2/3 instances est retenue sans label de confiance particulier. Comptage brut, sans jugement de cohérence. **3 appels par cycle.**

### P2 — Débat multi-instances (le baseline qui autorise le contact)
N=3 instances. Round 1 : identique à P1, chaque instance produit sa liste isolément. Round 2 : chaque instance reçoit sa propre sortie du round 1 **et** les sorties anonymisées des deux autres, avec instruction de réviser, confirmer ou retirer chaque assertion à la lumière de ce qu'ont vu les autres. Agrégation finale par le **même code que P1**, appliqué aux sorties du round 2 — pour que la seule variable entre P1 et P2 soit la présence ou l'absence de contact, pas la méthode d'agrégation. **6 appels par cycle (2 rounds × 3).**

Ce baseline existe parce que la littérature sur le débat multi-agents montre un risque documenté : le consensus qui émerge d'un débat peut converger vers la réponse la plus confiante plutôt que la plus correcte, particulièrement quand les instances partagent les mêmes biais de départ. Un résultat où P2 sous-performe P1 malgré le contact serait attendu par cette littérature, pas une anomalie du protocole.

### P3 — ETAU/SECS allégé
N=3 parseurs isolés (identique à P1 côté isolation), schéma contraint (`source_ref` obligatoire, pas de confiance individuelle), puis **un arbitre unique** qui reçoit uniquement les 3 sorties structurées, jamais le corpus brut (`R-ISOL-02`). L'arbitre applique une règle de cohérence, pas un seuil de comptage : une assertion portée par 1/3 mais assortie d'un raisonnement autonome vérifiable dans le `source_ref` peut être retenue `FORT`, tandis qu'une assertion portée par 2/3 sans justification distincte au-delà de la ressemblance thématique peut rester `FAIBLE`. Confiance assignée à l'arbitrage, jamais par un parseur sur sa propre sortie. Confiance binaire. Traçabilité au niveau du fil. **4 appels par cycle (3 parseurs + 1 arbitre).**

### P4 — ETAU/SECS complet
Trois étages, fidèles à la spécification native : N=3 parseurs isolés (round 1) → M=2 cartographes isolés (round 2, ne reçoivent que les sorties des parseurs) → un noyau de cohérence unique (round 3, ne reçoit que les sorties des cartographes). Confiance à trois niveaux : `FORT` (3/3), `PROBABLE` (2/3), `FAIBLE` (1/3 porté par argument autonome). Traçabilité à l'option B (niveau du fil, produite en round 2) — voir BR-003. **6 appels par cycle (3 + 2 + 1).**

**Adaptation nécessaire pour ce protocole, à documenter dans `ANALYSIS_PROTOCOL.md`** : en usage courant, les parseurs de passe 1 partitionnent un corpus volumineux. Pour ce banc d'essai, les 3 parseurs lisent chacun l'**intégralité** du corpus de test — condition nécessaire pour calculer un score de convergence par assertion. Ce n'est pas une redéfinition de la méthode, c'est un choix d'instrumentation.

**Total par cycle : 1 + 3 + 6 + 4 + 6 = 20 appels.** Avec 5 cycles répétés pour absorber la variance de température : ~100 appels au total, plus un volume marginal pour la mise en correspondance de BR-004 si l'option juge-LLM est retenue.

### 2bis. Isolation réelle — contrainte d'implémentation, pas de formulation de prompt

L'isolation ne se simule pas en demandant à un modèle de « faire semblant » d'être une instance isolée dans un même fil de conversation — le contexte partagé contamine silencieusement. L'isolation s'impose par le code (`R-ISOL-01`) :

```python
def isolated_call(client, model, prompt_fixe, corpus_text):
    messages = [{"role": "user", "content": f"{prompt_fixe}\n\n---\n{corpus_text}"}]
    assert len(messages) == 1, "violation d'isolation : contexte multi-tours détecté"
    return client.messages.create(model=model, max_tokens=2000, messages=messages)
```

Contrainte symétrique pour les arbitres/cartographes/noyau (`R-ISOL-02`) : leur fonction ne doit **pas avoir accès en paramètre** au texte du corpus brut — absence structurelle du paramètre dans la signature, vérifiable par lecture de code.

```python
def arbitrer(client, model, prompt_arbitrage, sorties_structurees_passe_precedente):
    # aucun paramètre corpus_text ici — impossible d'y accéder même par erreur
    ...
```

Pour P2 (débat), c'est l'inverse qui doit être vérifié (`R-CONTACT-01`) : un test confirme que les sorties des autres instances sont bien présentes dans le contexte du round suivant — sinon P2 dégénère silencieusement en P1 répété, et la comparaison devient invalide sans que rien ne le signale.

---

## 3. Corpus et vérité terrain

### Nature du corpus
Un corpus réel existant, au format `{session_id, tour_n, locuteur, texte}`, suffisamment court pour tenir dans un seul appel par instance. Le choix du corpus source est BR-001.

### Taxonomie des incidents injectés
Six types, injectés à des positions connues **avant** toute exécution de pipeline, dans `ground_truth.json` immuable une fois créé :

| Type | Ce qui est injecté | Comportement correct attendu |
|---|---|---|
| `CONTRADICTION_INTRA` | Un même locuteur affirme deux choses incompatibles dans la même session | Détectable par une seule instance, sans comparaison inter-instances |
| `CONTRADICTION_INTER` | Deux sessions distinctes affirment des faits incompatibles sur le même objet | Ne peut être détecté qu'à l'arbitrage/cartographie, jamais par un parseur isolé |
| `DERIVE` | Une affirmation hédée est reprise plus tard comme fait établi, sans nouvelle preuve | Test direct de la dérive épistémique |
| `NON_ETAYE` | Une affirmation à haute confiance apparente, sans source traçable dans le corpus | Signaler l'absence de fondement, pas juste la présence de contenu |
| `LACUNE_SILENCIEUSE` | Un sujet soulevé en début de corpus n'est jamais résolu, mais une session ultérieure agit comme s'il l'avait été | Signaler l'absence de résolution, pas la combler |
| `AMBIGU_GENUINE` | Deux lectures légitimes et non tranchables coexistent, sans qu'aucune ne soit fausse | Absence de clôture rapportée explicitement — forcer une résolution ici échoue le test |

Minimum 4 incidents par type, soit 24 au total.

### 3bis. Confidentialité de la taxonomie envers les pipelines

Aucune instance d'extraction, d'arbitrage, de cartographie ou de débat ne doit recevoir la liste des six types ci-dessus, ni savoir qu'il en existe exactement six, ni voir `ground_truth.json` sous quelque forme que ce soit (`R-SECRET-01`). Le prompt d'extraction fixe (identique pour toutes les architectures) demande une lecture générale à la recherche d'incohérences, de dérives ou d'absences de fondement — en langage ordinaire, pas en référence à une grille fermée. Une pipeline qui connaîtrait la taxonomie serait testée sur sa capacité à cocher six cases, pas sur sa capacité de détection réelle — c'est un résultat qui se prête à l'illusion de performance sans en avoir la substance.

### `generate_corpus.py` — étape 0, avant tout le reste
Lit le corpus source, injecte les incidents, écrit deux artefacts avant qu'aucune pipeline ne s'exécute : le corpus modifié, et `ground_truth.json` — jamais passé en paramètre à aucune pipeline, seulement à `metrics.py`.

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
| M02 | Localization Precision | détections dont le `source_ref` correspond exactement à l'incident réel / détections totales | « A vu qu'il y avait un problème » vs « sait où » |
| M03 | False Signal Rate | signaux ne correspondant à aucun incident injecté / signaux totaux | Le coût caché d'une détection agressive |
| M04 | Confidence Calibration | taux d'exactitude parmi `FORT` vs `FAIBLE` (P3/P4 seulement) | La confiance déclarée est-elle informative |
| M05 | Cost per Detection | (tokens + temps) / vrais positifs | Le prix réel de chaque architecture |
| M06 | Traceability Utility | test aveugle **manuel** : un testeur humain reçoit 8 assertions tirées au sort et chronomètre la recherche de la source exacte | Le vrai différenciateur de traçabilité (§1bis) |
| M07 | Clôture appropriée | sur `AMBIGU_GENUINE` uniquement : % rapportant une non-résolution plutôt qu'une fausse clôture | L'axiome de clôture stricte |
| M08 | Implementation Effort | lignes de code par pipeline, appels LLM par cycle | Faisabilité d'adoption |

M06 et M07 ne sont pas automatisables par l'agent de code seul et apparaissent dans le rapport comme `"required_manual_step": true` — jamais comme des champs vides silencieux.

---

## 5. Rôles — non-contamination du dispositif de test lui-même

Le dispositif expérimental est soumis à la règle qu'il teste : celui qui code les pipelines ne doit pas être celui qui juge les résultats.

- **Agent de code (Claude Code)** : construit les cinq pipelines, exécute, produit `results/`. Ne reçoit jamais `ground_truth.json` en entrée d'aucune pipeline.
- **Instance d'analyse, contexte séparé, jamais exposée au code ni aux prompts d'exécution** : reçoit uniquement `results/`, produit l'interprétation dans `reviews/REV-Sx.md`.
- **Arbitre final : l'auteur des méthodes.** Décide de l'application de la règle de pivot (§0) et tranche les BR (§6). Aucune instance IA ne décide du pivot à sa place.

### 5bis. Personas adversariaux

Avant qu'un livrable de sprint (code de pipeline en Sprint 3, résultats en Sprint 4) soit soumis à l'instance d'analyse, quatre sub-agents à posture distincte l'attaquent. Rôle repris de `methodologie-agentique-EIP-v3.1.md`, reconstruit ici pour le domaine de la vérification épistémique.

**Persona E — La Statisticienne de l'Évaluation**
Profil : évaluation de systèmes de classification, biais de mesure (fuite de label, surajustement).
- « Le champ `source_ref` est-il vérifié comme réellement présent et exact dans 100 % des sorties de P0-P4, ou seulement là où c'est « naturel » ? »
- « Le juge de correspondance de BR-004 a-t-il été calibré sur le même échantillon qui sert ensuite au score final, ou sur un échantillon disjoint ? S'il s'agit du même, le seuil est surajusté. »
- « M04 est-elle calculée sur un nombre d'assertions `FORT` suffisant pour que le taux ne soit pas dominé par 2-3 cas ? »

**Persona F — L'Ingénieure de la Reproductibilité**
Profil : même posture que dans la méthodologie source, appliquée à l'isolation plutôt qu'aux seeds numériques.
- « `R-ISOL-01` tourne-t-il réellement à chaque appel, ou seulement en Sprint 1 puis jamais revérifié ensuite ? »
- « Si le cycle est relancé demain avec le même corpus et la même graine, les cinq architectures produisent-elles des résultats identiques à la variance de température près, ou y a-t-il un état caché ? »

**Persona G — La Praticienne du Terrain**
Profil : consultante en gouvernance de connaissance qui devra justifier l'usage réel de l'architecture gagnante.
- « Si P3/P4 gagnent sur ce banc d'essai mais coûtent 6× plus cher (M05/M08), à partir de quel enjeu réel ce facteur devient-il justifiable pour un client ? »
- « La majorité des corpus réels tiennent-ils dans la contrainte d'un seul appel, ou faudra-t-il repartitionner avant d'appliquer ce résultat en production ? »

**Persona H — Le Critique de la Falsifiabilité**
Profil : même posture que le persona centré sur les hypothèses cachées dans la méthodologie source, appliquée à un protocole empirique plutôt qu'à une preuve.
- « Les six types d'incidents (§3) ont-ils été choisis, même inconsciemment, de manière à favoriser une architecture ? »
- « Si le résultat final est défavorable à ETAU/SECS, quel est le premier réflexe prévisible — accepter le résultat, ou chercher un septième type d'incident qui « aurait dû » être inclus ? Cette question a une réponse écrite avant le résultat, pas après : la réponse est R-PIVOT-01. »

**Porte de sortie** : si les quatre personas convergent sans friction réelle avec le livrable soumis, le risque est que les personas elles-mêmes partagent le biais de substrat de l'instance qui les exécute. Dans ce cas, recourir à une IA externe (Grok, Gemini ou Kimi, déjà utilisées ailleurs dans l'écosystème) pour un second passage. Décision à tracer une seule fois, dans BR-004 ou un BR dédié — pas à reposer à chaque sprint.

---

## 6. Décisions bloquantes — format BR

Rien en Sprint 0 ne peut commencer sans ces quatre décisions, tracées individuellement (`R-BR-01`).

### BR-001 — Corpus source
**Statut :** PROPOSÉ · **Décideur :** Sunu · **Council requis :** Non

Quel corpus réel sert de base ? S'il contient des données client ou institutionnelles sensibles, doit-il être anonymisé avant injection (noms de locuteurs, identifiants d'organisation) ? Un corpus destiné à un dépôt versionné, même privé, mérite cette question posée une fois plutôt que découverte après coup.

### BR-002 — Modèle et budget
**Statut :** PROPOSÉ · **Décideur :** Sunu · **Council requis :** Non

Un seul modèle pour les cinq architectures (`R-MODELE-01`). Lequel ? Budget attendu : 20 appels par cycle, ~100 pour 5 cycles (§2) — à confirmer avant de lancer.

### BR-003 — Traçabilité de P4
**Statut :** PROPOSÉ · **Décideur :** Sunu · **Council requis : OUI** (`R-COUNCIL-01` — deux options défendables, erreur coûteuse si le mauvais choix bloque Sprint 3 après coup)

L'option B (niveau du fil, produite en round 2) est prise par défaut pour permettre l'exécution du test. Ceci **ne tranche pas** la question de traçabilité ligne-à-ligne restée ouverte par ailleurs dans la spécification de la méthode — valeur provisoire testable, pas résolution définitive. Le Council (5 sous-agents) est invoqué avant Sprint 3 sur : « L'option B suffit-elle aux fins de ce banc d'essai, ou le choix affecte-t-il la validité des métriques M02/M06 au point de devoir trancher A/B/C définitivement d'abord ? »

### BR-004 — Mise en correspondance des assertions (P1/P2)
**Statut :** PROPOSÉ · **Décideur :** Sunu · **Council requis :** Non

**Option A — similarité d'embedding local.** Seuil de cosine à calibrer sur un échantillon disjoint de celui du score final (Persona E, §5bis). Coût : dépendance ML locale (`sentence-transformers` ou équivalent), lourde pour un environnement NixOS qui n'en a par ailleurs aucun besoin (§8bis).
**Option B — appel-juge à un modèle économique.** Prompt fixe, température=0, question binaire « ces deux assertions désignent-elles le même incident ? ». Coût : quelques appels supplémentaires, marginaux par rapport aux 20 appels principaux du cycle.
**Recommandation :** Option B — évite d'alourdir l'environnement pour un pipeline qui, par ailleurs, ne fait que du texte et du JSON.

---

## 7. Plan multi-sprints

**Note liminaire :** ce document est la source. Sprint 0 inclut la génération de `sprints/SPRINT-N-context.md` pour chacun des sprints ci-dessous — fichiers autonomes listant précisément les fichiers à lire et à ne pas lire pour cette session, à l'image de la pratique déjà établie ailleurs dans l'écosystème. En particulier, aucun fichier de contexte de sprint destiné aux pipelines d'extraction ne doit inclure la taxonomie de §3 (`R-SECRET-01`).

### Sprint 0 — Fondations
Squelette de dépôt (§8), `shell.nix` (§8bis), `generate_corpus.py`, `ground_truth.json`, BR-001 à BR-004 créés avec statut PROPOSÉ, fichiers `sprints/SPRINT-N-context.md`.
**Acceptation :** `ground_truth.json` existe, ≥24 incidents répartis sur les 6 types (≥4 chacun), graine fixée et documentée, référencé par aucun script de pipeline.

### Sprint 1 — P0 et P1
`pipeline_p0.py`, `pipeline_p1.py`, `common/isolation.py`, `common/agregation.py`. BR-004 tranchée avant ce sprint.
**Acceptation :** test automatisé confirme `R-ISOL-01` ; le mécanisme de BR-004 est implémenté et justifié dans un court rapport.

### Sprint 2 — P2
`pipeline_p2.py`, logs conservés par round.
**Acceptation :** test automatisé confirme `R-CONTACT-01`.

### Sprint 3 — P3 et P4
`pipeline_p3.py`, `pipeline_p4.py`. BR-003 tranchée (avec Council) avant ce sprint.
**Acceptation :** lecture de code confirme `R-ISOL-02` ; le label de confiance n'apparaît que dans la sortie finale de l'arbitre/noyau. **Personas E-H (§5bis) exécutées sur le code des quatre pipelines avant clôture du sprint.**

### Sprint 4 — Métriques
`metrics.py` calcule M01-M05, M08. Produit `metrics_report.json`, `summary.csv`.
**Acceptation :** `summary.csv` lisible directement par l'instance d'analyse ; M06/M07 marquées `"required_manual_step": true`. **Personas E-H exécutées sur les résultats avant passation. Grille SCORE-BE (§7bis) calculée pour la première fois.**

### Sprint 5 — Clôture et passation
`ANALYSIS_PROTOCOL.md` documentant l'adaptation de P4 (§2), les valeurs finales BR-001 à BR-004, tout écart entre ce document et ce qui a été codé. `STATUS.md` et `PROGRESSION.md` mis à jour. `results/` transmis à l'instance d'analyse séparée, jamais à l'agent qui a écrit le code.
**Acceptation :** quelqu'un qui n'a lu que `results/` et ce document peut reproduire la logique de scoring sans consulter le code source.

---

## 7bis. Grille de score par sprint — SCORE-BE

Calculée à partir de Sprint 4 (`R-SCORE-01`). Seuils identiques à la pratique déjà en place ailleurs : ≥80 GO · 65-79 GO conditionnel · 60-64 NO-GO · <60 NO-GO bloquant.

| Dimension | Points | Critères |
|---|---|---|
| Neutralité du protocole de mesure | 25 | `source_ref` obligatoire partout et vérifié ; BR-004 non surajustée ; aucune architecture avantagée par construction (§1bis) |
| Isolation vérifiée, pas déclarée | 25 | `R-ISOL-01`, `R-ISOL-02`, `R-CONTACT-01` passent en tests automatisés, pas seulement documentés |
| Reproductibilité | 20 | graine fixée, `shell.nix` versionné, un tiers peut relancer depuis le dépôt seul |
| Honnêteté sur les limites | 20 | §9 rempli sans édulcoration, adaptation P4 signalée dans `ANALYSIS_PROTOCOL.md`, `AMBIGU_GENUINE` non ajustés en faveur d'un résultat |
| Application effective de la règle de pivot | 10 | le verdict final applique §0 tel qu'écrit, sans reformulation post-hoc (`R-PIVOT-01`) |

---

## 8. Structure du dépôt

```
banc-essai/
├── README.md
├── CLAUDE.md
├── STATUS.md
├── CHANGELOG.md
├── PROGRESSION.md
├── requirements.txt
├── shell.nix
├── .gitignore
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
├── brainstorm/
│   ├── BR-001.md … BR-004.md
│   └── council-report-BR003.html
├── sprints/
│   └── SPRINT-0-context.md … SPRINT-5-context.md
├── reviews/
│   └── REV-S3.md, REV-S4.md, REV-FINAL.md
├── run_experiment.py
└── results/
    └── cycle_<n>/
        ├── raw_outputs/
        ├── metrics_report.json
        ├── summary.csv
        └── ANALYSIS_PROTOCOL.md
```

**Contraintes de livraison :** exécution en une seule commande (`python run_experiment.py --cycles 5`), aucun input interactif, chaque pipeline dans son propre fichier, chaque décision de formule non triviale commentée dans le code — en particulier le mécanisme de BR-004 et la règle de cohérence de l'arbitre P3/P4.

---

## 8bis. Environnement NixOS

`shell.nix` à la racine. Dépendances volontairement légères : ce banc d'essai ne fait que du texte, du JSON et des appels API — pas d'entraînement, pas de tenseurs, donc pas de `pytorch` ni de bibliothèque d'embeddings locale (cohérent avec la recommandation Option B de BR-004).

```nix
# shell.nix — Environnement reproductible pour le banc d'essai ETAU/SECS
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.pandas
    python312Packages.numpy
    python312Packages.pytest
    python312Packages.requests
  ];

  shellHook = ''
    if [ ! -d .venv ]; then
      python -m venv .venv
    fi
    source .venv/bin/activate
    pip install --quiet anthropic
    echo "✅ Environnement banc d'essai activé"
    echo "   Python : $(python --version)"
  '';
}
```

Le SDK `anthropic` n'est pas empaqueté dans nixpkgs — installation via un `.venv` local activé par le `shellHook`, jamais par un `pip install` hors de `nix-shell`.

**`.gitignore` obligatoire avant le premier `git add`** — pattern déjà rencontré ailleurs comme leçon apprise après coup, appliqué ici en amont plutôt qu'en correction :

```
.venv/
__pycache__/
.cache/
result result-*
*.pyc
```

**Garde-fous à reprendre si un script de déploiement est ajouté** : fichier individuel > 50 Mo → push bloqué ; pack git > 95 Mo → push bloqué avec indication de nettoyage d'historique. Non critique pour ce projet (pas de poids de modèle, pas de gros binaires) mais peu coûteux à poser dès Sprint 0.

**Environnement alternatif, si nécessaire hors NixOS :** `requirements.txt` (anthropic, pandas, numpy, pytest, requests) + `python -m venv .venv` classique. Non prioritaire tant que l'exécution reste sur l'environnement documenté ci-dessus.

---

## 9. Ce que ce protocole ne teste pas

Il ne teste pas ETAU/SECS sur un corpus volumineux avec partition réelle (§2, adaptation P4). Il ne teste pas la robustesse à un changement de modèle (`R-MODELE-01` fixe un seul modèle par construction). Il ne teste pas le coût humain de supervision du protocole lui-même, seulement le coût machine (M08 ne compte pas le temps de l'arbitre final humain). Il ne mesure pas si les erreurs détectées auraient été trouvées de toute façon par une relecture humaine ordinaire — ce protocole compare des architectures IA entre elles, pas une architecture IA à un statu quo humain.

---

## 10. Questions ouvertes, non bloquantes pour Sprint 0

- Une fois un premier cycle exécuté, faut-il faire varier N (3 → 5) comme second facteur expérimental, ou est-ce prématuré avant un premier résultat sur N=3 ?
- Le choix de l'option B pour BR-003 reste provisoire. Si Sprint 3-4 montre que P4 ne dépasse pas P3 de façon notable, la question de trancher A/B/C définitivement perd une partie de son urgence.
- Faut-il répéter le cycle complet avec un second modèle une fois qu'un premier résultat existe, pour vérifier qu'il n'est pas un artefact du modèle choisi en BR-002 ? Non prioritaire avant un premier passage complet.
- Si le Council de BR-003 et les personas de Sprint 3 convergent tous sans friction : est-ce un signe que le protocole est solide, ou que les deux mécanismes partagent un biais commun avec l'instance qui les exécute (cf. porte de sortie, §5bis) ? Cette question n'a pas de réponse a priori — à observer.

---

*Document v0.2 — modifications tracées dans le changelog (§0). Statut : prêt pour Sprint 0 sous réserve de BR-001 à BR-004. Document autonome pour exécution agentique — ne suppose aucun contexte de conversation antérieur.*
