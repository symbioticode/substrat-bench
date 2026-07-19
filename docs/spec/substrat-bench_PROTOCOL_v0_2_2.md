# Banc d'essai ETAU/SECS — Protocole multi-sprints pour exécution agentique

*Document destiné à un agent de code (Claude Code). Le cadrage, l'architecture et les critères d'acceptation sont fixés ici — l'agent n'a pas à interpréter l'objectif. L'agent code, exécute, loggue. Il ne juge pas les résultats : voir §5 sur la séparation des rôles.*

> **Version 0.2.2** — Fusion contrôlée. Base : v0.2 (référence normative, numérotation P1=débat/P2=vote faisant foi). Amendements v0.2 d'origine, quatre choses ajoutées sur v0.1 :
> (1) un **second facteur expérimental** — diversification par personas (Cycles A/B), appliqué symétriquement à toutes les architectures pour ne pas casser la logique d'attribution de D2 ;
> (2) une **métrique M09** — taux de miss corrélé, qui capture spécifiquement la signature du biais monosubstrat ;
> (3) une **porte de sortie conditionnelle** vers un second modèle (Cycle C), avec règle de déclenchement fixée avant tout résultat ;
> (4) une **recommandation D2** orientée free tiers en API directe, coût cible : zéro.
> Motivation documentée en §0bis. Les sections modifiées portent la mention **[Ajout v0.2]** ou **[Modifié v0.2]**.
>
> **Ajouts v0.2.2**, intégrés depuis une réécriture parallèle (v0.2.1) après vérification qu'ils n'entraient en conflit avec aucun invariant ci-dessus : métrique **M10** (Persona Delta Recall, définie précisément — §4) ; séparation `common/schemas.py` / `common/prompts.py` (Sprint 1) ; utilitaire `scripts/lab_status.sh` ; un `ANALYSIS_PROTOCOL.md` par cycle plutôt qu'un seul partagé (§8). **Rejeté explicitement de v0.2.1** : l'inversion de la numérotation P1/P2, la suppression du §1quater (Cycle C conditionnel), la suppression de l'Annexe A verbatim, la suppression du rôle "rédacteur des personas" (§5). Ce document (v0.2.2) est désormais la seule référence normative — toute session d'agent doit repartir de lui, jamais d'un fichier `*v0_2_1*` ou antérieur.

---

## 0. Cadrage

Ce protocole ne cherche pas à démontrer la supériorité d'ETAU/SECS sur une alternative. Il répond à des questions, avec une règle de décision fixée avant tout résultat — pas après.

**Question 1** : à isolation égale entre instances, la structure propre à ETAU/SECS (schéma de sortie contraint, confiance graduée, arbitrage par cohérence plutôt que par vote, traçabilité obligatoire) détecte-t-elle et localise-t-elle davantage d'erreurs réelles qu'un simple vote majoritaire sur les mêmes instances isolées — et à quel coût supplémentaire ?

**Question 2**, orthogonale : l'isolation elle-même compte-t-elle ? On compare des instances qui ne se voient jamais (vote majoritaire, ETAU/SECS) à des instances qui se voient et révisent leur réponse au fil de rounds successifs.

**Question 3 [Ajout v0.2]**, orthogonale aux deux premières : la diversification des postures de lecture (personas) compense-t-elle partiellement le biais de substrat unique imposé par D2 ? Concrètement : des instances du même modèle, dotées de postures épistémiques distinctes, ratent-elles moins souvent *toutes ensemble* le même incident que des instances au prompt uniforme ? Cette question a un précédent empirique dans le corpus de l'auteur : la méthodologie EIP documente (LA-EIP-15) qu'un panel de 4 personas internes n'a pas vu une faille qu'un panel multi-modèles a trouvée. Les personas atténuent le biais de substrat ; ils ne l'éliminent pas. Ce protocole mesure l'ampleur de l'atténuation au lieu de la supposer.

**Règle de pivot (fixée maintenant, non négociable après coup)**
- Si le vote majoritaire égale ou dépasse ETAU/SECS en détection et localisation, à coût inférieur → le vote majoritaire devient la méthode par défaut ; ETAU/SECS devient une option pour les cas où la traçabilité a de la valeur indépendamment de la détection.
- Si la version allégée d'ETAU/SECS égale la version complète → la granularité fine de confiance est un raffinement non prioritaire, pas un invariant à défendre.
- Un résultat où une architecture gagne en détection mais perd en coût n'est pas tranché de force. Les deux chiffres sont rapportés tels quels.
- **[Ajout v0.2]** Si le Cycle B (personas) rattrape ou dépasse l'écart que P3/P4 creusent sur P2 en Cycle A — autrement dit, si un vote majoritaire à personas diversifiés égale un ETAU/SECS à prompts uniformes — ce résultat est rapporté tel quel et pèse dans l'arbitrage final : il signifierait que la diversification de lecture est un levier moins coûteux que la sophistication d'arbitrage. Le protocole doit être prêt à l'encaisser.

**Ce que ce protocole n'est pas** : un test d'ETAU/SECS en conditions réelles sur un corpus de production. C'est un banc d'essai contrôlé, avec vérité terrain injectée et connue à l'avance — condition nécessaire pour que "détection" et "précision" signifient quelque chose. Un test sur corpus réel sans vérité terrain ne mesure que du volume de signal, jamais son exactitude.

---

## 0bis. Motivation des amendements v0.2 [Ajout v0.2]

Le protocole v0.1 fixe un seul modèle pour les cinq architectures (D2) — contrainte correcte pour attribuer tout écart à l'architecture. Mais elle installe un risque connu et documenté dans le corpus de l'auteur (leçon SecAudit : deux instances du même provider forment une chambre d'écho ; Zhang et al. 2025 : l'hétérogénéité des providers est le seul levier empiriquement robuste) : des instances du même substrat partagent les mêmes angles morts. Le danger n'est pas le bruit — il est le **miss corrélé** : les N instances ratent le même incident parce que le modèle lui-même ne peut pas le voir, et le 0/N se déguise en absence confirmée. Aucune métrique de v0.1 ne distingue ce cas d'une vraie absence.

Deux clarifications de périmètre, pour éviter toute surinterprétation du résultat :

- **Ce banc teste des architectures de type SECS** (analyse d'un corpus clos, où la variance entre instances vient de l'échantillonnage). Pour cette classe de tâche, le mono-modèle + personas est une configuration défendable, et c'est précisément ce que le Cycle B mesure.
- **Ce banc ne dit rien sur ETAU en usage natif** (exploration ouverte, deep search). Là, les flux interrogent le contenu du substrat d'entraînement lui-même : un persona change l'angle d'interrogation, pas le contenu interrogé. Deux flux ETAU sur le même modèle violent l'esprit de l'axe 1 (indépendance des sources), personas ou pas. La réponse pour ETAU n'est pas dans ce banc — elle est dans l'hétérogénéité des providers, désormais accessible à coût nul via les free tiers en API directe (voir §6, note D2). Cette limite est reprise en §9.

---

## 1. Cinq architectures, pas deux

Le test ne compare pas "ETAU/SECS vs une alternative". Il croise des axes indépendants, pour isoler ce qui produit réellement un effet :

| | Isolation stricte (aucune instance ne voit la sortie d'une autre avant sa propre clôture) | Contact autorisé (les instances se voient et révisent) |
|---|---|---|
| **Sortie libre, arbitrage par comptage** | **P2** — vote majoritaire | **P1** — débat multi-instances |
| **Schéma contraint, arbitrage par cohérence, traçabilité obligatoire** | **P3 / P4** — ETAU/SECS (allégé / complet) | *(non testé — combinaison défendue par aucune des deux méthodologies)* |

**P0** est hors tableau : une seule instance, aucun ensemble, sert de plancher de référence.

**[Ajout v0.2] Numérotation faisant foi.** Ce document et le document antérieur `etau_secs_vs_base_trivial.md` ne numérotent pas les pipelines de la même façon (dans l'antérieur : P1 = vote majoritaire, P2 = SECS complet). **La grille de ce document fait foi** : P0 = passe unique, P1 = débat, P2 = vote majoritaire, P3 = ETAU/SECS allégé, P4 = ETAU/SECS complet. `ANALYSIS_PROTOCOL.md` (§7, Sprint 5) doit restater cette grille en tête de fichier — l'instance d'analyse séparée ne doit jamais avoir à deviner quelle convention s'applique.

Un seul modèle, identique pour les cinq architectures, sur l'ensemble de l'expérience. C'est une contrainte non négociable : tout écart de résultat doit être attribuable à l'architecture, jamais à un facteur confondant de modèle.

### 1bis. Un biais de mesure à corriger avant d'écrire une ligne de code

Le score final (Recall, Précision — §4) dépend d'une mise en correspondance entre ce qu'une architecture rapporte et la vérité terrain. Si seules P3/P4 sont contraintes de citer une source exacte (session_id, tour_n) et que P0/P1/P2 rapportent en texte libre, le matching pour P0/P1/P2 devient approximatif (nécessite un appariement sémantique bruité), pendant que P3/P4 bénéficient d'un matching exact. Le résultat serait alors biaisé en faveur d'ETAU/SECS par construction du protocole, pas par mérite de la méthode.

**Correction imposée à toutes les architectures, y compris P0/P1/P2** : chaque assertion produite par n'importe quelle pipeline doit inclure un champ `source_ref` obligatoire (`session_id`, `tour_n`). Ce champ est syntaxique — il ne demande à aucune instance de raisonner sur la fiabilité de sa source, juste de citer où elle a lu ce qu'elle rapporte. Toutes les architectures peuvent le produire sans effort supplémentaire notable.

Cette correction déplace le vrai test de traçabilité : ce n'est plus "qui cite une source" (égal partout désormais) mais "la source citée permet-elle réellement de retrouver et vérifier l'assertion sans ambiguïté, et le chemin de preuve remonte-t-il jusqu'à l'origine" — c'est exactement M06 (§4), pas M01-M03.

### 1ter. Second facteur : diversification par personas — Cycles A et B [Ajout v0.2]

Le facteur personas est appliqué **symétriquement à toutes les architectures**, jamais à une seule. Injecter des personas dans les parseurs de P3/P4 sans en donner aux instances de P1/P2 créerait un facteur confondant : impossible ensuite de savoir si un écart vient de la structure ETAU/SECS ou de la diversification des prompts. Le dispositif est donc un plan croisé :

| Cycle | Prompts des N instances de lecture | Ce qui est mesuré |
|---|---|---|
| **Cycle A** | Uniformes — le protocole v0.1 tel quel | Baseline de référence, toutes métriques |
| **Cycle B** | Chacune des N=3 instances reçoit un des trois personas de l'Annexe A — les **trois mêmes personas dans toutes les pipelines** | Effet de la diversification de lecture, toutes métriques, M09 en particulier |

**Où les personas s'appliquent — et où ils ne s'appliquent pas.** Les personas ne concernent que le **niveau de lecture du corpus** : les N instances de P1 (round 1), les N instances de P2, les N parseurs de P3 et de P4. Ils ne s'appliquent **jamais** aux étages d'agrégation et d'arbitrage : l'arbitre de P3, les cartographes et le noyau de P4 gardent leurs prompts v0.1 uniformes dans les deux cycles. Raisons : (a) P1/P2 n'ont pas d'instance d'arbitrage (agrégation par code) — un persona d'arbitre briserait la symétrie ; (b) le facteur testé est la diversification de la *lecture*, pas de l'*arbitrage* ; mélanger les deux rendrait le résultat ininterprétable. P0 reste identique dans les deux cycles (une seule instance, prompt uniforme) — c'est le plancher, il ne bouge pas.

**Mécanique d'implémentation.** Le persona est un préfixe de system/prompt injecté par `isolated_call` (voir §2bis, signature amendée). L'attribution persona→instance est fixe et documentée (instance 1 = Vérificateur, instance 2 = Traceur, instance 3 = Cartographe), identique dans toutes les pipelines et tous les cycles B — pas de tirage aléatoire, pour que les comparaisons inter-pipelines portent sur les mêmes triplets de postures.

**Effet attendu et honnêteté du dispositif.** En Cycle B, le vote majoritaire de P2 change subtilement de nature : deux personas différents qui convergent constituent déjà un début de recoupement de perspectives, pas un simple ré-échantillonnage de température. Si P2-Cycle-B rattrape P4-Cycle-B, c'est un résultat défavorable à la sophistication d'arbitrage — et il est couvert par la règle de pivot (§0, quatrième tiret). Le protocole ne protège aucune des deux issues.

### 1quater. Porte de sortie : Cycle C conditionnel, second modèle [Ajout v0.2]

Règle fixée maintenant, avant tout résultat. Le Cycle C (répétition du cycle complet avec un **second modèle**, personas actifs, toutes pipelines) est déclenché si et seulement si, à l'issue des Cycles A et B :

> le taux de miss corrélé agrégé (M09, toutes pipelines à ensemble confondues) du Cycle B ne baisse pas d'au moins **un tiers en relatif** par rapport au Cycle A, **ou** reste supérieur ou égal à **25 % des incidents injectés** en valeur absolue.

Interprétation de la règle : si les personas réduisent nettement les angles morts partagés, le mono-modèle + personas est validé comme configuration acceptable pour les tâches de type SECS, et le second modèle reste une extension optionnelle. Si les personas n'y suffisent pas, le biais de substrat est démontré actif sur ce corpus, et seul un second substrat peut le mesurer — la question ouverte n°3 de v0.1 (§10) devient alors obligatoire, pas facultative. Le second modèle est choisi parmi les free tiers en API directe (critères en §6, note D2) : la porte de sortie ne coûte rien. Ce mécanisme est le pendant exact de la "porte de sortie" documentée dans la méthodologie EIP (recours aux IA externes quand les personas convergent avec l'instance de travail), transposé en règle quantitative.

---

## 2. Les cinq architectures — algorithme exact

Constantes partagées : N = 3 instances par ensemble, R = 2 rounds pour le débat, M = 2 instances de second niveau pour P4. Valeurs modifiables mais fixées identiques pour toute la durée d'un cycle de test — ne pas ajuster N en cours de route. **[Ajout v0.2]** N = 3 est aussi le nombre de personas de l'Annexe A — les deux constantes sont couplées par construction ; si N change un jour, l'Annexe A doit être révisée en conséquence.

### P0 — Passe unique (plancher)
Une instance, un appel, contexte vierge, corpus entier en entrée. Produit une liste libre d'assertions avec `source_ref`. Aucun ensemble, aucune confiance déclarée. Sert à mesurer ce qu'apporte le simple fait d'avoir plusieurs instances, avant même de discuter d'architecture. **[Ajout v0.2]** Identique en Cycles A et B.

### P2 — Vote majoritaire (le baseline qui doit être pris au sérieux)
N instances, isolation stricte identique à P3/P4 — **l'isolation n'est pas la variable testée ici, seule la structure de sortie l'est**. Chaque instance reçoit un contexte frais (voir §2bis), le corpus entier, un prompt d'extraction fixe identique pour les trois **[Modifié v0.2 : en Cycle B, le prompt d'extraction reste identique mais chaque instance reçoit en préfixe son persona attribué — voir §1ter]**, et produit une liste libre d'assertions avec `source_ref`. Agrégation **par code, pas par une instance IA** : deux assertions dont le `source_ref` coïncide et dont le texte dépasse un seuil de similarité sémantique (embedding cosine, seuil à fixer en Sprint 1) sont regroupées. Une assertion portée par ≥2/3 instances est retenue sans label de confiance particulier — juste "retenue" ou "rejetée" sur seuil de comptage. C'est le comptage brut, sans jugement de cohérence.

### P1 — Débat multi-instances (le baseline qui autorise le contact)
N instances. Round 1 : identique à P2, chaque instance produit sa liste isolément **[Modifié v0.2 : en Cycle B, personas au round 1 uniquement — les rounds de révision 2..R gardent le persona de l'instance, mais aucune instruction supplémentaire liée aux personas n'est ajoutée aux consignes de révision]**. Round 2 à R : chaque instance reçoit sa propre sortie du round précédent **et** les sorties anonymisées des autres instances, avec instruction de réviser, confirmer ou retirer chaque assertion à la lumière de ce qu'ont vu les autres. Après le round R, agrégation par le **même code d'agrégation que P2** (comptage, seuil identique) sur les sorties du dernier round — pour que la seule variable entre P1 et P2 soit la présence ou l'absence de contact inter-instances, pas la méthode d'agrégation finale.

Ce baseline existe parce que la littérature sur le débat multi-agents montre un risque documenté : le consensus qui émerge d'un débat peut converger vers la réponse la plus confiante plutôt que la plus correcte, particulièrement quand les instances partagent les mêmes biais de départ. Un résultat où P1 sous-performe P2 malgré (ou à cause) du contact serait un résultat attendu par cette littérature, pas une anomalie du protocole.

### P3 — ETAU/SECS allégé
N parseurs isolés (identique à P2 côté isolation), schéma contraint (`source_ref` obligatoire, pas de champ de confiance individuel — voir ci-dessous), puis **un arbitre unique** qui reçoit uniquement les N sorties structurées des parseurs, jamais le corpus brut. L'arbitre applique une règle de cohérence, pas un simple seuil de comptage : une assertion portée par 1/N mais assortie d'un raisonnement autonome vérifiable dans le `source_ref` peut être retenue avec un label `FORT`, tandis qu'une assertion portée par 2/N sans justification distincte au-delà de la ressemblance thématique peut rester `FAIBLE`. C'est ici, à l'arbitrage, que la confiance est assignée — jamais par un parseur sur sa propre sortie. Confiance binaire : `FORT` / `FAIBLE`. Traçabilité au niveau du fil (pas de la ligne individuelle). **[Ajout v0.2]** En Cycle B : personas sur les N parseurs uniquement ; l'arbitre reste au prompt v0.1. L'arbitre n'est pas informé de quel persona a produit quelle sortie — les sorties structurées lui parviennent anonymisées comme en v0.1, sinon il pourrait pondérer par posture au lieu de juger par cohérence.

### P4 — ETAU/SECS complet
Trois étages, fidèles à la spécification native : N parseurs isolés (round 1) → M cartographes isolés (round 2, ne reçoivent que les sorties structurées des parseurs, jamais le corpus brut) → un noyau de cohérence unique (round 3, ne reçoit que les sorties des cartographes). Confiance à trois niveaux : `FORT` (N/N), `PROBABLE` ((N-1)/N), `FAIBLE` (1/N porté par argument autonome). Traçabilité choisie à l'option B (niveau du fil, produite en round 2) — voir §6, décision D3. **[Ajout v0.2]** En Cycle B : personas sur les N parseurs uniquement ; cartographes et noyau restent aux prompts v0.1, sorties de parseurs anonymisées quant au persona (même règle que P3).

**Adaptation nécessaire pour ce protocole, à documenter explicitement dans le rapport final** : en usage courant, les N parseurs de passe 1 partitionnent un corpus volumineux (chacun lit une portion différente). Pour ce banc d'essai, les N parseurs lisent chacun l'**intégralité** du corpus de test — condition nécessaire pour calculer un score de convergence par assertion. Ce n'est pas une redéfinition de la méthode, c'est un choix d'instrumentation pour la rendre mesurable ; à signaler comme tel dans `ANALYSIS_PROTOCOL.md` (§7).

### 2bis. Isolation réelle — contrainte d'implémentation, pas de formulation de prompt

L'isolation ne se simule pas en demandant à un modèle de "faire semblant" d'être une instance isolée dans un même fil de conversation — le contexte partagé contamine silencieusement, même sans mention explicite des autres instances. L'isolation s'impose par le code : chaque appel isolé construit une liste `messages` fraîche, à un seul élément, sans historique de conversation antérieur.

**[Modifié v0.2]** La signature accepte un persona optionnel. Le persona est un préfixe textuel — il ne change rien à la contrainte d'isolation, et l'assertion reste identique :

```python
def isolated_call(client, model, prompt_fixe, corpus_text, persona=None):
    prefixe = f"{persona}\n\n" if persona else ""
    messages = [{"role": "user", "content": f"{prefixe}{prompt_fixe}\n\n---\n{corpus_text}"}]
    assert len(messages) == 1, "violation d'isolation : contexte multi-tours détecté"
    return client.messages.create(model=model, max_tokens=2000, messages=messages)
```

Contrainte symétrique pour les arbitres/cartographes/noyau : leur fonction ne doit **pas avoir accès en paramètre** au texte du corpus brut — pas "instruction de ne pas s'en servir", mais absence structurelle du paramètre dans la signature de la fonction, vérifiable par lecture de code. **[Ajout v0.2]** Même logique pour les personas : les fonctions d'arbitrage/cartographie/noyau n'ont **pas de paramètre `persona`** dans leur signature — l'impossibilité structurelle, pas l'instruction.

```python
def arbitrer(client, model, prompt_arbitrage, sorties_structurees_passe_precedente):
    # aucun paramètre corpus_text ni persona ici — impossible d'y accéder même par erreur
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
| `DERIVE` | Une affirmation hédgée ("il semble que...") est reprise plus tard comme fait établi, sans nouvelle preuve | Test direct de la dérive épistémique documentée par ailleurs |
| `NON_ETAYE` | Une affirmation à haute confiance apparente, sans aucune source traçable dans le corpus | Test de la capacité à signaler l'absence de fondement, pas juste la présence de contenu |
| `LACUNE_SILENCIEUSE` | Un sujet soulevé comme important en début de corpus n'est jamais résolu, mais une session ultérieure agit comme s'il l'avait été | Analogue textuel d'un silence porteur de signal — la bonne réponse est de signaler l'absence de résolution, pas de la combler |
| `AMBIGU_GENUINE` | Deux lectures légitimes et non tranchables coexistent dans le corpus, sans qu'aucune ne soit fausse | La bonne réponse est l'absence de clôture, rapportée explicitement — une architecture qui force une résolution ici échoue le test même si sa réponse "semble" raisonnable |

Minimum 4 incidents par type, soit 24 au total, pour que les métriques de §4 aient un sens statistique en dessous du bruit d'échantillonnage.

**[Ajout v0.2] Légitimité des personas vis-à-vis de la taxonomie.** Les personas de l'Annexe A sont dérivés des *classes* d'échec épistémique de cette taxonomie — laquelle est publique dans le présent protocole — jamais des *positions* d'injection, qui restent secrètes dans `ground_truth.json`. Ce n'est pas du teaching to the test : un déploiement réel de la méthode concevrait ses postures de lecture exactement de la même façon, à partir des classes d'erreur qu'elle vise. La frontière à ne jamais franchir : quiconque rédige ou ajuste un persona ne doit pas avoir vu `ground_truth.json`. Les personas sont figés à Sprint 0, avant toute injection.

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
| **M09** **[Ajout v0.2]** | **Taux de miss corrélé** | incidents détectés par **0/N instances de lecture** / incidents injectés — voir définition exacte ci-dessous | **La signature du biais monosubstrat : l'angle mort partagé, invisible pour M01 qui ne distingue pas "raté par une instance" de "raté par toutes"** |
| **M10** **[Ajout v0.2.2]** | **Persona Delta Recall** | Δ Recall = Recall(Cycle B, pipeline X) − Recall(Cycle A, pipeline X), calculé séparément pour chaque pipeline à ensemble (P1, P2, P3, P4) | **L'effet net, en Recall, de la diversification par personas — complète M09 (qui mesure le miss corrélé en amont) par une mesure en aval, sur le score final agrégé** |

**[Ajout v0.2] Définition exacte de M09.** M09 se mesure au niveau des **sorties brutes des instances de lecture, avant toute agrégation** : les N sorties d'instances de P2, les N sorties de round 1 de P1 (le round 1 uniquement — mesurer après contact confondrait angle mort de lecture et effet de convergence du débat), les N sorties de parseurs de P3 et de P4. Un incident est en miss corrélé pour une pipeline si aucune de ses N sorties de lecture ne le mentionne (matching identique à M01/M02 : `source_ref` + similarité sémantique au seuil D4). M09 est rapporté : (a) par pipeline ; (b) agrégé sur les pipelines à ensemble (P1 round 1, P2, P3, P4) — c'est la valeur agrégée qui alimente la règle de déclenchement du Cycle C (§1quater) ; (c) ventilé par type d'incident, parce qu'un miss corrélé concentré sur un seul type (par exemple `DERIVE`) est un diagnostic plus actionnable qu'un taux global. P0 est exclu de M09 par construction (une seule instance : tout miss y est trivialement "corrélé"). La comparaison décisive est **M09-Cycle-A vs M09-Cycle-B**, à pipeline égale.

M06 et M07 ne sont pas automatisables par l'agent de code seul. M06 requiert un humain ; M07 requiert que le testeur humain confirme manuellement, sur l'échantillon `AMBIGU_GENUINE`, que la lecture du corpus est réellement indécidable et pas juste mal rédigée — sinon la métrique mesure la qualité de la rédaction du corpus, pas la méthode. **[Ajout v0.2]** M09, en revanche, est entièrement automatisable : il réutilise le matching de M01/M02 sur des sorties déjà loguées. **[Ajout v0.2.2]** M10 l'est également, à condition que M01 (Recall) ait déjà été calculé séparément pour Cycle A et Cycle B sur chaque pipeline — M10 est alors une simple soustraction, calculée après coup par `metrics.py`, jamais par une instance IA. Un M10 positif et notable sur P1/P2 (baselines) mais proche de zéro sur P3/P4 indiquerait que les personas compensent surtout l'absence de structure d'arbitrage — résultat en tension avec un M09 qui baisserait uniformément ; les deux métriques doivent être lues ensemble, pas substituées l'une à l'autre.

---

## 5. Rôles — non-contamination du dispositif de test lui-même

Le dispositif expérimental est soumis à la même règle qu'il teste : celui qui code les pipelines ne doit pas être celui qui juge les résultats.

- **Agent de code (Claude Code, ce document)** : construit les cinq pipelines, exécute, produit `results/`. Ne reçoit jamais `ground_truth.json` en entrée d'aucune pipeline — seulement `metrics.py` y accède, en aval, une fois les sorties déjà figées.
- **Instance d'analyse, contexte séparé, jamais exposée au code ni aux prompts d'exécution** : reçoit uniquement le contenu de `results/`, produit l'interprétation. Si la même instance a écrit le code des pipelines ET analyse leurs résultats, l'analyse est structurellement suspecte — pas par malveillance, par la même logique qui interdit à un parseur isolé de s'auto-arbitrer.
- **Arbitre final : l'auteur des méthodes.** Décide de l'application de la règle de pivot (§0) **[Ajout v0.2 : et de la règle de déclenchement du Cycle C (§1quater) — la règle est quantitative, mais sa constatation et son exécution restent humaines]**. Aucune instance IA ne décide du pivot à sa place.
- **[Ajout v0.2] Rédacteur des personas : l'auteur des méthodes, à Sprint 0, avant toute injection.** Ni l'agent de code ni les personas eux-mêmes ne sont modifiés après la création de `ground_truth.json`. Tout ajustement de persona après un premier résultat invalide les Cycles déjà courus pour la comparaison A/B — il ouvre un nouveau cycle, il ne corrige pas l'ancien.

---

## 6. Décisions bloquantes avant Sprint 0

Rien en Sprint 0 ne peut commencer sans ces quatre réponses.

- **D1 — Corpus source.** Quel corpus réel sert de base ? S'il contient des données client ou institutionnelles sensibles, doit-il être anonymisé avant injection (noms de locuteurs, identifiants d'organisation) ? Un corpus destiné à un dépôt versionné, même privé, mérite cette question posée une fois plutôt que découverte après coup.
- **D2 — Modèle et budget.** Un seul modèle pour les cinq architectures (§1, contrainte non négociable). Lequel ? Budget approximatif attendu : ~23 appels LLM par cycle complet sur le corpus (1 pour P0, 6 pour P1, 6 pour P2, 4 pour P3, 6 pour P4). **[Modifié v0.2]** Avec 5 répétitions par cycle pour absorber la variance de température, et le plan croisé A/B, le budget devient : Cycle A ~115 appels + Cycle B ~115 appels = **~230 appels**, plus ~115 conditionnels si le Cycle C se déclenche (§1quater). **Recommandation v0.2 : un free tier en API directe, coût cible zéro.** Critères de sélection, dans l'ordre : (1) fenêtre de contexte suffisante pour le corpus entier en un seul appel avec marge ; (2) fiabilité du JSON structuré en sortie (à valider par un smoke test de 5 appels avant de figer D2) ; (3) rate limits compatibles avec ~25 appels séquentiels par run sans attente pathologique ; (4) API directe, aucun gateway intermédiaire. Candidats à évaluer le jour du lancement (les quotas des free tiers changent — vérifier, ne pas supposer) : Gemini via AI Studio, Groq, Cerebras, Mistral La Plateforme. Le modèle du Cycle C, s'il a lieu, est choisi dans la même liste, en excluant le modèle de D2 et en privilégiant la famille d'entraînement la plus éloignée. Noter dans `ANALYSIS_PROTOCOL.md` la contrepartie assumée : un free tier peut impliquer que les données envoyées servent à l'entraînement du fournisseur — acceptable pour un corpus anonymisé destiné à un dépôt versionné (D1), à re-vérifier si D1 change.
- **D3 — Traçabilité de P4.** L'option B (niveau du fil, produite en round 2) est prise par défaut ici, uniquement pour permettre l'exécution de ce test. Ceci **ne tranche pas** la question de traçabilité ligne-à-ligne restée ouverte par ailleurs dans la spécification de la méthode — ce document choisit une valeur provisoire testable, pas une résolution définitive.
- **D4 — Seuil de similarité sémantique** pour l'agrégation par code de P1/P2 (§2). Une valeur par défaut sera proposée en Sprint 1 à partir d'un échantillon manuel, mais elle doit être validée avant d'être figée pour tout le cycle. **[Ajout v0.2]** Le même seuil D4 sert au matching de M09 — une seule valeur, partagée, jamais deux seuils distincts pour l'agrégation et pour la mesure.

---

## 7. Plan multi-sprints

### Sprint 0 — Fondations
Squelette de dépôt (§8), `requirements.txt`, `generate_corpus.py`, `ground_truth.json`. **[Ajout v0.2]** Plus : `prompts/personas/` contenant les trois personas de l'Annexe A, recopiés verbatim, figés avant la génération de `ground_truth.json` (ordre imposé par §3 et §5).
**Critère d'acceptation** : `ground_truth.json` existe, contient ≥24 incidents répartis sur les 6 types (≥4 chacun), est généré avec une graine aléatoire fixée et documentée (reproductibilité), et n'est référencé par aucun script de pipeline — seulement par `metrics.py`. **[Ajout v0.2]** Les trois fichiers persona existent, leur hash est logué dans `PROGRESSION.md` à Sprint 0, et le commit qui les crée précède le commit qui crée `ground_truth.json`.

### Sprint 1 — P0 et P1 (baselines sans structure)
`pipeline_p0.py`, `pipeline_p1.py`, `common/isolation.py`, `common/agregation.py` (le module de comptage partagé entre P1 et P2). **[Ajout v0.2]** `common/isolation.py` implémente la signature amendée de §2bis (paramètre `persona=None`) et le flag global `--personas on|off` est câblé dès ce sprint. **[Ajout v0.2.2]** `common/schemas.py` (validation JSON des sorties, y compris `source_ref` obligatoire — §1bis) et `common/prompts.py` (texte des prompts d'extraction fixes) sont créés dès ce sprint, même si P3/P4 ne les consomment qu'en Sprint 3 — éviter qu'un prompt d'extraction diverge entre pipelines faute d'être centralisé dès le départ.
**Critère d'acceptation** : un test automatisé confirme qu'aucun appel isolé ne reçoit plus d'un message dans son historique (assertion de §2bis exécutée, pas seulement documentée) ; le seuil de similarité D4 est fixé et justifié dans un court rapport. **[Ajout v0.2]** Un test confirme qu'en mode `--personas off`, aucun contenu des fichiers persona n'apparaît dans aucun prompt envoyé (vérification par recherche de sous-chaîne sur les logs bruts) — le Cycle A doit être un vrai v0.1, pas un Cycle B au persona vide.

### Sprint 2 — P2 (débat, contact autorisé)
`pipeline_p2.py`, logs conservés **par round**, pas seulement la sortie finale.
**Critère d'acceptation** : un test automatisé confirme que le contexte du round 2 contient bien littéralement les sorties du round 1 des autres instances (pas seulement de la sienne) — la vérification inverse de celle du Sprint 1.

*Note v0.2 : le titre v0.1 de ce sprint désignait le débat par "P2" — coquille de numérotation par rapport à sa propre grille du §1. Grille faisant foi (§1) : le débat est P1, le vote majoritaire est P2. Le contenu du sprint (pipeline de débat, logs par round) est inchangé ; seul le libellé est aligné.*

### Sprint 3 — P3 et P4 (ETAU/SECS)
`pipeline_p3.py`, `pipeline_p4.py`. Implémente D3.
**Critère d'acceptation** : lecture de code confirme que les fonctions d'arbitrage/cartographie n'ont structurellement aucun paramètre `corpus_text` **[Ajout v0.2 : ni `persona`]** dans leur signature (§2bis) ; le label de confiance n'apparaît que dans la sortie finale de l'arbitre/noyau, jamais dans les sorties individuelles des parseurs. **[Ajout v0.2]** Un test confirme que les sorties de parseurs transmises à l'arbitre/aux cartographes ne contiennent aucun marqueur permettant d'identifier le persona d'origine (anonymisation de §2, P3/P4).

### Sprint 4 — Métriques
`metrics.py` calcule M01-M05, M08 **[Modifié v0.2 : et M09]** pour les cinq pipelines sur les 24+ incidents. Produit `metrics_report.json` et `summary.csv`.
**Critère d'acceptation** : `summary.csv` lisible directement par l'instance d'analyse (§5) sans traitement supplémentaire ; M06 et M07 apparaissent dans le rapport comme `"required_manual_step": true`, pas comme des champs vides silencieux — l'absence d'automatisation doit être visible, pas masquée. **[Ajout v0.2]** M09 apparaît par pipeline, en agrégé, et ventilé par type d'incident (§4) ; `summary.csv` contient une colonne `cycle` (`A`/`B`/`C`) pour que la comparaison inter-cycles se fasse sans retraitement.

### Sprint 5 — Clôture et passation
`ANALYSIS_PROTOCOL.md` documentant : l'adaptation de P4 signalée en §2 (parseurs redondants plutôt que partition), les valeurs finales de D1-D4, tout écart entre ce document et ce qui a réellement été codé. **[Ajout v0.2]** Plus : la grille de numérotation faisant foi (§1), restatée en tête de fichier ; les hashes des trois personas ; le constat chiffré de la règle du Cycle C (§1quater) — déclenchée ou non, avec les deux valeurs de M09 agrégé qui la décident ; la contrepartie free tier de D2 (usage des données par le fournisseur) si applicable. `PROGRESSION.md` mis à jour. Dossier `results/` transmis à l'instance d'analyse séparée (§5), jamais à l'agent qui a écrit le code.
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
├── prompts/
│   └── personas/
│       ├── persona_verificateur.md
│       ├── persona_traceur.md
│       └── persona_cartographe.md
├── pipelines/
│   ├── common/
│   │   ├── isolation.py
│   │   ├── agregation.py
│   │   ├── schemas.py        # [Ajout v0.2.2] schémas de sortie contrainte (P3/P4), validation JSON
│   │   └── prompts.py        # [Ajout v0.2.2] prompts d'extraction fixes, séparés du code d'orchestration
│   ├── pipeline_p0.py
│   ├── pipeline_p1.py
│   ├── pipeline_p2.py
│   ├── pipeline_p3.py
│   └── pipeline_p4.py
├── metrics/
│   └── metrics.py
├── scripts/
│   └── lab_status.sh          # [Ajout v0.2.2] état des lieux rapide : cycles exécutés, provider actif, résumé SETUP_LOG.md
├── run_experiment.py
└── results/
    ├── cycle_A_<n>/
    │   ├── raw_outputs/
    │   ├── metrics_report.json
    │   ├── summary.csv
    │   └── ANALYSIS_PROTOCOL.md   # [Ajout v0.2.2] une copie par cycle, plus sûr qu'un seul fichier partagé en cas de comparaison a posteriori
    ├── cycle_B_<n>/
    │   └── (même structure)
    └── cycle_C_<n>/            # créé seulement si §1quater déclenche
        └── (même structure)
```

**[Ajout v0.2.2]** `common/schemas.py` et `common/prompts.py` séparent respectivement la validation de sortie et le texte des prompts d'extraction du code d'orchestration des pipelines — pas un changement de logique, une meilleure organisation pour Sprint 1. `scripts/lab_status.sh` est un utilitaire de confort (état des lieux en une commande), il ne remplace aucun critère d'acceptation des sprints §7.

**Contraintes de livraison** : exécution en une seule commande, aucun input interactif, chaque pipeline dans son propre fichier, chaque décision de formule non triviale commentée dans le code — en particulier la formule de similarité sémantique (D4) et la règle de cohérence de l'arbitre P3/P4, qui ne sont pas de simples seuils et méritent d'être justifiées en ligne. **[Modifié v0.2]** Interface de commande :

```
python run_experiment.py --cycles 5 --personas off   # Cycle A
python run_experiment.py --cycles 5 --personas on    # Cycle B
python run_experiment.py --full                      # A puis B, séquentiels
# Cycle C : mêmes commandes avec --model <second_modele>, lancé manuellement
# par l'arbitre final si et seulement si la règle de §1quater est constatée
```

Le Cycle C n'est **jamais** déclenché automatiquement par le code — la constatation de la règle appartient à l'arbitre final (§5).

---

## 9. Ce que ce protocole ne teste pas

Il ne teste pas ETAU/SECS sur un corpus volumineux avec partition réelle (§2, adaptation P4). Il ne teste pas la robustesse à un changement de modèle (D2 fixe un seul modèle par construction — un résultat favorable ici pourrait être un artefact de ce modèle précis, pas une propriété générale de l'architecture ; **[Ajout v0.2]** le Cycle C conditionnel entrouvre cette porte, mais un second modèle sur un corpus ne fait pas une généralité — il fait un second point de mesure). Il ne teste pas le coût humain de supervision du protocole lui-même, seulement le coût machine (M08 ne compte pas le temps de l'arbitre final humain). Il ne mesure pas si les erreurs détectées auraient été trouvées de toute façon par une relecture humaine ordinaire — ce protocole compare des architectures IA entre elles, pas une architecture IA à un statu quo humain.

**[Ajout v0.2]** Il ne teste pas non plus :
- **ETAU en usage natif (deep search).** Le résultat des Cycles A/B porte sur des tâches d'analyse de corpus clos (classe SECS). Il ne transfère pas aux flux d'exploration ouverte d'ETAU, où l'indépendance des sources exige des substrats d'entraînement distincts — un persona change l'angle d'interrogation, pas le contenu interrogé (§0bis). Conclure de "les personas suffisent pour SECS" à "les personas suffisent pour ETAU" serait une surgénéralisation explicitement rejetée par ce document.
- **La généralité des trois personas de l'Annexe A.** Ils sont dérivés de la taxonomie des six incidents (§3). Un corpus aux classes d'erreur différentes exigerait des postures différentes ; ce banc mesure l'effet de *cette* triade sur *cette* taxonomie, pas l'effet des personas en général.
- **L'interaction personas × contact.** En Cycle B, P1 (débat) mélange deux effets — diversification de lecture et convergence de débat. M09 est mesuré au round 1 précisément pour isoler le premier ; l'effet du contact sur des instances à personas différents après le round 1 est observable dans les logs mais n'est l'objet d'aucune métrique dédiée.

---

## 10. Questions ouvertes, non bloquantes pour Sprint 0

- Une fois un premier cycle exécuté, faut-il faire varier N (3 → 5) comme second facteur expérimental, ou est-ce prématuré avant d'avoir un premier résultat sur N=3 ? **[Note v0.2]** Si N passe à 5, l'Annexe A doit être étendue à 5 personas — le couplage est documenté en §2.
- Le choix de l'option B pour D3 (§6) reste provisoire. Si le résultat de Sprint 3-4 montre que P4 ne dépasse pas P3 de façon notable, la question de trancher entre les options A/B/C ailleurs perd une partie de son urgence — un résultat négatif ici est aussi une réponse utile à cette question distincte.
- **[Modifié v0.2]** ~~Faut-il répéter le cycle complet avec un second modèle une fois qu'un premier résultat existe ?~~ Cette question n'est plus ouverte : elle est formalisée en règle conditionnelle (§1quater, Cycle C). Reste ouverte sa suite : si le Cycle C se déclenche *et* confirme le biais de substrat, faut-il faire de l'hétérogénéité de modèle une contrainte de déploiement de SECS (et pas seulement d'ETAU) ? Décision d'arbitre final, hors périmètre du banc.
- **[Ajout v0.2]** Les personas de l'Annexe A attribuent une posture par instance. Une alternative non testée ici : un persona unique "multi-postures" donné aux trois instances (chacune reçoit les trois consignes d'attention). L'hypothèse de v0.2 est que la spécialisation par instance produit plus de diversité effective que la juxtaposition dans un même prompt — hypothèse plausible, non démontrée, à tester si les Cycles A/B laissent la question ouverte.

---

## Annexe A — Les trois personas de lecture [Ajout v0.2]

Règles d'usage : (1) recopiés verbatim dans `prompts/personas/`, figés à Sprint 0 avant la création de `ground_truth.json` ; (2) injectés uniquement au niveau de lecture (§1ter), en préfixe du prompt d'extraction commun, qui reste identique aux trois instances ; (3) aucun persona ne mentionne la taxonomie de §3 par ses noms de types — il encode une *posture*, pas une checklist de la grille de correction ; (4) rédigés pour rester compatibles avec le schéma de sortie de chaque pipeline (libre pour P1/P2, contraint pour P3/P4) — le persona oriente l'attention, il ne modifie jamais le format demandé.

### A.1 — Le Vérificateur de cohérence interne (`persona_verificateur.md`)

> Tu lis ce corpus avec une discipline unique : la mémoire des engagements. Chaque fois qu'un locuteur affirme quelque chose, tu retiens ce qu'il a déjà affirmé — dans cette session et dans les autres — et tu confrontes systématiquement le nouveau au déjà-dit. Une affirmation n'existe jamais seule : elle est compatible, redondante ou incompatible avec ce qui précède, et c'est cette relation qui t'intéresse. Tu accordes une attention égale aux incompatibilités entre sessions différentes qu'aux incompatibilités au sein d'une même session : deux passages éloignés qui parlent du même objet doivent être confrontés comme s'ils étaient adjacents. Quand deux passages sont en tension, tu le rapportes même si la tension est peut-être explicable — signaler une tension n'est pas accuser, c'est documenter. Tu ne combles jamais une incompatibilité par une interprétation charitable qui la ferait disparaître.

### A.2 — Le Traceur de provenance (`persona_traceur.md`)

> Tu lis ce corpus avec une question unique, posée à chaque affirmation : d'où sait-on ça ? Pour chaque assertion rencontrée, tu cherches son fondement dans le corpus lui-même — une source citée, une observation rapportée, un raisonnement explicite. Tu distingues rigoureusement trois statuts : fondé (le chemin vers la preuve existe dans le corpus), déclaré-sans-fondement (affirmé avec assurance, mais aucun chemin), et dérivé-d'une-hypothèse (le fondement existe mais c'était une supposition, pas un fait — et tu vérifies si le passage du statut d'hypothèse au statut de fait s'est accompagné d'une preuve nouvelle, ou s'est fait en silence). Le ton assuré d'une affirmation ne compte pour rien dans ton évaluation ; seul compte le chemin de preuve. Une affirmation confiante sans fondement est précisément ce que tu es là pour voir.

### A.3 — Le Cartographe des fils ouverts (`persona_cartographe.md`)

> Tu lis ce corpus en tenant l'inventaire de ce qui a été ouvert et de ce qui a été fermé. Chaque question soulevée, chaque sujet annoncé comme important, chaque décision annoncée comme à prendre est un fil — et tu suis chaque fil jusqu'à sa résolution explicite ou jusqu'à la fin du corpus. Un fil jamais refermé est un fait à rapporter, pas un vide à combler : tu ne complètes jamais mentalement une résolution qui n'est pas écrite. Tu es particulièrement attentif aux passages qui *agissent comme si* un fil était résolu sans que la résolution figure nulle part — c'est la forme la plus silencieuse de fermeture fictive. Et quand deux lectures d'un même passage sont légitimes et qu'aucun élément du corpus ne permet de trancher, tu rapportes l'ambiguïté comme telle : forcer une clôture que le texte ne donne pas est, de ton point de vue, une erreur plus grave que laisser une question ouverte.

**Note de conception, à conserver dans `ANALYSIS_PROTOCOL.md`** : la triade couvre les six types de la taxonomie sans les nommer — Vérificateur → contradictions intra/inter ; Traceur → non-étayé et dérive ; Cartographe → lacunes silencieuses et ambiguïtés génuines. Le recouvrement n'est pas exclusif (un Traceur peut voir une contradiction) et c'est voulu : les personas orientent l'attention, ils ne partitionnent pas la responsabilité. Un incident vu par les trois malgré la spécialisation est un signal de robustesse, pas une anomalie.

---

## Changelog

- **v0.2.2** — Fusion contrôlée post-incident : intégration de M10 (défini précisément, sur le modèle de M09 — §4), `common/schemas.py` + `common/prompts.py` (Sprint 1, §7 et §8), `scripts/lab_status.sh` (§8), `ANALYSIS_PROTOCOL.md` par cycle plutôt que partagé (§8). Numérotation P1=débat/P2=vote, §1quater (Cycle C) et Annexe A conservés intacts depuis v0.2 — non renégociables, une tentative de réécriture parallèle (v0.2.1) les avait supprimés/inversés sans mandat.
- **v0.2** — Amendements additifs : Question 3 et quatrième tiret de la règle de pivot (§0) ; motivation et périmètre SECS/ETAU (§0bis) ; correction de la grille de numérotation P1/P2 dans le tableau du §1 pour la rendre conforme aux définitions du §2, note "numérotation faisant foi" vis-à-vis de `etau_secs_vs_base_trivial.md` ; facteur Cycles A/B (§1ter) ; règle de déclenchement du Cycle C (§1quater) ; personas au niveau lecture seulement, anonymisés en aval (§2, P1-P4) ; signature `isolated_call` avec `persona=None` et interdiction structurelle du paramètre `persona` en arbitrage (§2bis) ; légitimité des personas vis-à-vis de la taxonomie (§3) ; métrique M09 avec définition exacte (§4) ; rôle "rédacteur des personas" et extension du rôle d'arbitre final (§5) ; D2 recadré free tiers avec critères et budget ~230 appels, D4 partagé avec M09 (§6) ; sprints 0-5 amendés, alignement du libellé du Sprint 2 (§7) ; `prompts/personas/` et structure `results/` par cycle, CLI `--personas` (§8) ; trois non-tests supplémentaires (§9) ; question ouverte n°3 fermée en règle, deux nouvelles ouvertes (§10) ; Annexe A. Correction orthographique : "hédée" → "hédgée" (§3).
- **v0.1** — Première formalisation.

---

*Document v0.2.2 — fusion contrôlée, seule référence normative du projet substrat-bench. Statut : prêt pour Sprint 0 sous réserve des décisions D1-D4 (§6) — D2 dispose désormais d'une recommandation par défaut (free tier, critères listés) qui reste à valider par smoke test le jour du lancement. Document autonome pour exécution agentique — ne suppose aucun contexte de conversation antérieur. Tout agent d'exécution (Nemotron, Claude Code ou autre) traite ce fichier en LECTURE SEULE : toute incohérence perçue se signale dans `SETUP_LOG.md`, ne se corrige jamais silencieusement dans ce fichier.*
