# Passage de substrat-bench v0.2.2 à v0.3.0

**Date :** 2026-08-15

**Branche de travail :** `codex/huang-budget-matched-20260815`

**Référence précédente :** `substrat-bench_PROTOCOL_v0_2_2.md`

**Nouvelle référence normative :** `substrat-bench_PROTOCOL_v0_3_0.md`

## Origine de la correction

Le banc est né d'une objection formulée avant publication d'ETAU et SECS :
une architecture d'isolation, d'arbitrage et de traçabilité peut être élégante
sans battre une baseline qui génère plusieurs réponses indépendantes et prend
la majorité.

La référence retrouvée est Huang et al., *Large Language Models Cannot
Self-Correct Reasoning Yet* (ICLR 2024, arXiv:2310.01798). Sa section 4 compare
le débat multi-agents à la self-consistency. Sur GSM8K, le débat paraît
légèrement meilleur qu'une baseline à trois réponses, mais utilise déjà six
réponses ; à six puis neuf réponses de part et d'autre, la self-consistency par
vote majoritaire le dépasse. La leçon expérimentale retenue est donc :
**comparer à nombre de réponses égal**.

## Lacune de v0.2.2

La v0.2.2 conservait bien l'adversaire simple P2, M09/M10 et une règle de
pivot défavorable à SECS si nécessaire. Cependant :

- P1 consommait six réponses contre trois pour P2 ;
- P3 en consommait quatre et P4 six, toujours contre P2 à trois réponses ;
- M05 enregistrait un coût mais sa formule additionnait des unités
  incompatibles (`tokens + temps`) ;
- la mention D2 de six appels P2 et 23 appels totaux ne correspondait pas à
  l'algorithme P2, qui n'en spécifiait que trois.

La v0.2.2 répondait donc à une question pratique de compromis
performance/coût, mais ne pouvait pas confirmer ou infirmer proprement le
contrôle de Huang. Présenter P1 contre P2 comme une comparaison où seul le
contact variait était inexact.

## Correction v0.3.0

P2 produit désormais un lot unique de six lectures indépendantes. Ses
préfixes donnent trois contrôles sans nouvel appel :

| Comparaison | Réponses méthode | Contrôle | Réponses contrôle |
|---|---:|---|---:|
| P1 débat | 6 | P2@6 | 6 |
| P3 SECS allégé | 4 | P2@4 | 4 |
| P4 SECS complet | 6 | P2@6 | 6 |

P2@3 reste la baseline native historique. Toute comparaison contre elle à
budget différent reste publiée mais marquée `budget_inegal` et ne peut fonder
le verdict principal.

M05 devient un vecteur : appels, tokens d'entrée, tokens de sortie, temps mur
et USD sont rapportés séparément, par vrai positif. Un registre append-only
conserve une ligne par appel. Une égalité en réponses n'étant pas forcément
une égalité en tokens, les deux axes restent visibles.

## Ce qui ne change pas

- P1 reste le débat et P2 le vote majoritaire.
- M09 et M10 restent des mesures centrales des angles morts corrélés et de
  l'effet des personas.
- Les Cycles A/B et la porte conditionnelle vers Cycle C restent en place.
- Le contrôle Huang primaire est conduit en Cycle A ; la taxonomie demeure
  publique, seules les positions exactes de la vérité terrain sont cachées.
- Le résultat porte sur une tâche SECS de corpus clos. Il ne mesure pas ETAU
  en exploration ouverte.
- La gouvernance BR/Council et les personas d'audit de code évoqués dans une
  révision parallèle sont des couches d'exécution complémentaires, pas des
  variables ajoutées au dispositif expérimental v0.3.0.

## Portée du résultat futur

Même corrigé, ce banc ne sera pas une réplication de Huang : corpus, sorties
multi-label et métriques diffèrent de GSM8K. Il pourra tester la **validité
externe** de leur résultat sur la détection d'incidents épistémiques. Une
victoire ou une défaite de SECS devra être bornée à ce corpus, ce modèle et ce
budget.
