# Pilote P0 direct Anthropic↔DeepSeek

**Date :** 2026-08-10 · **Branche :** `codex/omniroute-autonome-20260810`

## Périmètre honnête

Ce lot compare le plancher P0 sur deux providers directs. Il ne constitue ni
les Cycles A/B, ni M09, ni le Cycle C normatif : `origin/main` ne versionne pas
encore le corpus/ground truth requis et P0 n'a qu'une instance de lecture.

## Protocole

- même corpus pilote figé de 12 tours et cinq zones attendues;
- Sonnet 4.5 snapshot et DeepSeek V4 Flash;
- cinq répétitions par modèle, température 0, appels séquentiels;
- fenêtre autorisée 00:00–04:00 America/Toronto;
- budgets durs 1,50 USD/provider, écriture du manifeste après chaque appel;
- caches natifs mesurés; aucune couche Omniroute.

## Résultats

| Provider | Succès | Assertions/run | Sorties distinctes | Médiane | Coût conservateur |
|---|---:|---|---:|---:|---:|
| Anthropic | 5/5 | 14,14,14,14,14 | 5/5 | 11,210 s | 0,081105 USD |
| DeepSeek | 5/5 | 15,15,20,15,15 | 5/5 | 7,442 s | 0,023939 USD |

Fréquence descriptive de détection sur cinq runs :

| Zone attendue | Sonnet | DeepSeek | Union inter-provider |
|---|---:|---:|---:|
| Contradiction budget | 5/5 | 5/5 | 5/5 |
| Dérive date | 5/5 | 5/5 | 5/5 |
| Affirmation non étayée | 5/5 | 5/5 | 5/5 |
| Lacune paiement | 5/5 | 1/5 | 5/5 |
| Ambiguïté genuine | 5/5 | 0/5 | 5/5 |

Le second provider apporte donc ici une information réelle : DeepSeek partage
un angle mort stable sur l'ambiguïté et détecte rarement la lacune paiement,
alors que Sonnet les signale à chaque répétition. Ce constat est un diagnostic
sur ce petit corpus, pas une mesure de supériorité générale.

## Cache et consommation

- Anthropic : 4 975 tokens entrée, 4 412 sortie; cache création/lecture = 0.
  Le prompt d'environ 995 tokens est sous le minimum Sonnet 4.5 de 1 024;
  aucun padding artificiel n'a été ajouté pour provoquer un hit.
- DeepSeek : 1 293 tokens miss et 3 072 hit sur 4 365 entrée; 4 517 sortie.
- Les prix utilisés pour les caps sont conservateurs : 3/15 USD/MTok pour
  Sonnet et 1/5 pour DeepSeek, bien au-dessus du tarif V4 Flash affiché.

## Garde-fous vérifiés

- 7 tests légers passés;
- thinking DeepSeek explicitement désactivé;
- manifeste reprenable et mis à jour appel par appel;
- aucun fichier du worktree sale historique n'a été inclus;
- analyse JSON marque `descriptive_only_not_m09: true`.

## Prochaine étape normative

Versionner d'abord un corpus/ground truth validé de ≥24 incidents, exécuter les
cinq Cycles A et cinq Cycles B sur un modèle unique, calculer M09/M10, puis
laisser Andrei constater la condition de déclenchement du Cycle C. Le présent
résultat indique que restaurer un second provider vaut la peine, mais ne saute
aucun de ces gates.
