## 1. Protocole de test — ETAU/SECS vs baseline trivial

Je reprends le format du D-SIG Stress Test, adapté à votre cas. L'esprit est identique au vôtre : pas de théorie, on injecte de la vérité terrain connue, on mesure, et la règle de pivot est déjà écrite avant de lancer quoi que ce soit.

> **Note** : Ce document décrit une comparaison simplifiée à 4 pipelines (P0-P3). Le protocole complet multi-sprints à 5 architectures (P0-P4, avec débat multi-instances P2 comme axe orthogonal) est dans `ETAU_SECS_banc_essai_multisprint_v0_1.md`. Ce document ne teste pas l'axe "contact vs isolation" (P2 du multisprint) — seulement "vote majoritaire isolé vs ETAU/SECS".

### Objectif
Déterminer si l'isolation séquentielle + granularité de confiance + traçabilité inversable d'ETAU/SECS détecte et localise plus d'erreurs/divergences réelles qu'un baseline trivial (vote majoritaire sans isolation soignée), à budget de calcul comparable — et si l'écart, s'il existe, justifie le coût d'ingénierie supplémentaire.

### Nature du corpus — condition non négociable
Le problème central de tout test sur ETAU/SECS : vos corpus réels (brainstormings LocalContext, sessions TI-360) **n'ont pas de vérité terrain connue**. Sans vérité terrain, "SECS a trouvé 3 divergences que le baseline n'a pas trouvées" ne prouve rien — vous ne savez pas si ces 3 divergences sont réelles ou fabriquées par le protocole lui-même.

Il faut donc deux corpus distincts, pas un seul :

**Corpus A — synthétique, vérité terrain injectée.** Vous prenez un corpus réel existant (une session TI-360, ou un fil de brainstorming LocalContext) et vous y injectez délibérément N erreurs factuelles, contradictions et dérives connues à l'avance : une déclaration qui contredit une déclaration antérieure du même locuteur, un chiffre modifié entre deux mentions, une affirmation non étayée présentée comme un fait établi, un cas exact du pattern "dérive épistémique" que vous avez déjà documenté (déclarations d'un liaison person passant de β=N honnête à projection non vérifiée). Chaque injection est loggée dans un fichier séparé (`ground_truth.json`) **avant** exécution, avec position exacte (session_id, tour_n) et type d'erreur. Personne — humain ou IA — ne voit ce fichier avant l'analyse finale.

**Corpus B — réel, sans vérité terrain, usage qualitatif seulement.** Un corpus réel non modifié sert à mesurer le comportement en conditions naturelles (volume de signal détecté, coût, latence) mais jamais à mesurer une précision — puisqu'on ne sait pas ce qui est vrai.

Sans corpus A, le test ne vaut rien. C'est le point le plus important de ce protocole.

### Pipelines à comparer (4, comme votre logique OTel→D-SIG)

| Pipeline | Description |
|---|---|
| P0 — Single-pass | Une instance lit le corpus une fois, produit une synthèse libre. Baseline plancher. |
| P1 — Self-consistency / vote majoritaire | 3 instances, **isolation stricte identique à P2/P3**, même prompt, la synthèse retenue est celle qui recoupe au moins 2/3. C'est le baseline sérieux (Huang et al.). |
| P2 — SECS/ETAU complet | Isolation réelle (contexte frais par instance, pas de persona jouée dans un même thread), granularité de confiance à 3 niveaux, arbitrage par cohérence, traçabilité au format que vous avez choisi (option A/B/C de l'axe 5 — trancher avant de lancer le test, pas pendant). |
| P3 — SECS/ETAU allégé | Version minimale évoquée dans mon audit précédent : isolation réelle + confiance binaire (fort/faible) + traçabilité au niveau du fil, pas de la ligne. Sert à vérifier si la sophistication fine de P2 ajoute quelque chose par rapport à P3. |

P3 est important et absent de vos documents actuels : sans lui, vous ne pourrez jamais savoir si c'est l'isolation qui fait le travail ou la granularité fine.

### Critères / métriques

| Métrique | Description | Calcul | Vérité terrain requise |
|---|---|---|---|
| Detection Recall | % des erreurs injectées effectivement signalées | erreurs détectées / erreurs injectées | Oui |
| Localization Precision | % des erreurs détectées correctement localisées (bon tour, bon locuteur) | — | Oui |
| False Signal Rate | % de "divergences" signalées qui ne correspondent à aucune erreur injectée | — | Oui |
| Confidence Calibration | Les erreurs marquées "signal fort" sont-elles réellement plus souvent correctes que celles marquées "signal faible" ? | corrélation confiance déclarée / exactitude réelle | Oui |
| Cost per Detection | tokens + temps / erreurs correctement détectées | compteur direct | Non |
| Traceability Utility | un humain peut-il, à partir du fichier final seul, retrouver la source exacte de chaque assertion sans relire le corpus ? | test aveugle : 5 assertions tirées au hasard, chronomètre pour les retracer | Non, mais nécessite un testeur humain naïf |
| Non-recoupement informatif | quand P2/P3 signalent "pas de convergence" sur une zone, est-ce que cette zone contient effectivement une ambiguïté réelle (pas juste du bruit d'isolation) ? | vérification manuelle sur échantillon | Oui, partiellement |

Les trois premières métriques sont celles qui décident tout. Le reste est utile mais secondaire.

### Rôles
Reprenez exactement votre structure D-SIG (définition / exécution / analyse séparées pour éviter le conflit d'intérêt) :
- **Vous** : injectez la vérité terrain, seul à la connaître, arbitre final.
- **Une instance** : exécute les 4 pipelines sur le corpus A, aveugle à la vérité terrain.
- **Une seconde instance, dans un contexte totalement séparé** : compare les sorties des 4 pipelines au fichier `ground_truth.json` et calcule les métriques. Cette instance ne doit jamais avoir vu le corpus brut ni les prompts d'exécution — sinon vous recréez exactement le biais de contamination que vos propres invariants interdisent.

### Règle de pivot (déjà écrite, comme vous le demandez)
- Si P1 égale ou dépasse P2 sur Detection Recall et Localization Precision, à Cost per Detection inférieur : vous pivotez vers P1, ETAU/SECS devient un raffinement optionnel pour les cas à enjeu de traçabilité (audit, gouvernance), pas la méthode par défaut.
- Si P2 ne dépasse pas P3 significativement : la granularité fine (axe 3, 3 niveaux) est du raffinement prématuré, retour à P3 comme version de référence.
- Seul un écart sur Detection Recall **et** Localization Precision, pas seulement sur l'un des deux, justifie de garder P2 tel quel.

### Corpus candidat immédiat
Vous avez déjà un corpus réel avec un cas de dérive documenté (le liaison person β=N → projection non vérifiée). C'est un excellent candidat pour le corpus A : vous connaissez déjà l'endroit exact de la dérive, il suffit de l'isoler proprement dans un fichier de vérité terrain séparé et d'ajouter quelques erreurs synthétiques supplémentaires pour avoir un échantillon N suffisant (minimum 15-20 erreurs injectées pour que Detection Recall soit statistiquement lisible).

