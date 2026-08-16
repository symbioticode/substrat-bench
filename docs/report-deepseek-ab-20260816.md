# Rapport du run DeepSeek A+B du 2026-08-16 — tentative r1 invalidée

## Verdict

La tentative `results/deepseek-v4-flash-ab-20260816-r1` est **invalidée**.
Elle a été arrêtée après une répétition Cycle A complète et le premier appel de
la répétition suivante, lorsqu'une sortie P4 techniquement acceptée mais
scientifiquement vide a été constatée.

Ce run ne permet aucune conclusion sur l'effet des personas, sur la comparaison
Cycle A contre Cycle B, sur le débat P1 contre le vote P2, ni sur l'hypothèse de
Huang. Les valeurs intermédiaires ne sont pas des résultats scientifiques.

## Distinction avec les gates préalables

Les gates d'adaptation consignés dans
`docs/deepseek-d2-gates-20260816.md` ont vérifié séparément l'accès au modèle,
le parsing JSON, la capacité mécanique de 32 assertions, les pipelines pris
isolément et le calcul de M09. Ils ne constituent pas le run A+B.

La présente tentative est le premier dossier destiné au run scientifique
complet. Elle devait contenir 230 réponses : 23 réponses par répétition, cinq
répétitions en Cycle A et cinq en Cycle B. Elle n'a pas atteint ce contrat.

## État quantitatif vérifié

Le registre contient 24 lignes sur les 230 attendues :

| Cycle | Répétition | Pipeline | Appels |
|---|---:|---|---:|
| A | 0 | P0 | 1 |
| A | 0 | P1 | 6 |
| A | 0 | P2 | 6 |
| A | 0 | P3 | 4 |
| A | 0 | P4 | 6 |
| A | 1 | P0 | 1 |

La répétition `A0` a donc consommé les 23 appels préenregistrés. Seul P0 a été
exécuté dans `A1` avant l'arrêt.

Totaux validés directement depuis `inference_ledger.jsonl` :

- tokens entrants : **340 787** ;
- tokens sortants : **69 997** ;
- temps mur cumulé des appels : **362 801,615 ms** ;
- coût estimé conservateur : **0,06730934 USD** ;
- provider/modèle : `deepseek` / `deepseek-v4-flash` sur les 24 lignes ;
- seed effectif : `null` sur les 24 lignes, conformément au contrat D2.

Aucun code HTTP 429 n'est inscrit dans les artefacts disponibles. L'arrêt est
motivé par la non-conformité fonctionnelle de P4, pas par une limitation de
débit documentée.

## Preuve négative P4

Le résumé `cycle_A_0/cycle_summary.json` déclare :

- trois parseurs P4 ;
- deux cartographes P4 ;
- six appels P4 consommés ;
- `assertions_final: 0` ;
- `non_convergence_zones: 0`.

Les deux fichiers cartographes contiennent chacun `clusters: []`. Ils incluent
en revanche des fragments ressemblant à une assertion individuelle. Le premier
n'a pas de `dialogue_act`; le second porte un acte `Hypothesize`. Cette forme ne
respecte pas le contrat attendu d'une cartographie de clusters. Le noyau a reçu
ces sorties, puis `p4_nucleus_cycle0.jsonl` est resté vide. Le fichier de
non-convergence contient `[]`.

L'événement AGNOS de P4 indique « terminé sans exception ». Il prouve seulement
l'absence d'exception Python : il ne prouve pas une sortie P4 exploitable. Cette
tentative met donc en évidence un défaut de gate sémantique : une chaîne P4 vide
peut actuellement être enregistrée comme succès technique.

Pour mémoire, les autres sorties intermédiaires de `A0` indiquent 32 assertions
pour P0, 23 assertions finales pour P1, 32 pour la vue native P2 rapportée par le
résumé et 17 pour P3. Ces nombres ne doivent pas être comparés comme scores : le
calcul final contre la vérité terrain n'a pas été produit et la répétition
appartient à un run invalidé.

## Métriques absentes et conclusions interdites

À l'arrêt, le dossier ne contient ni `metrics_report.json` ni `summary.csv` à sa
racine. Le flux AGNOS ne contient pas d'événement terminal pour
`substrat-runner`; son dernier événement démarre P1 de la répétition `A1`.

En conséquence :

- M01 à M08 ne sont pas disponibles comme rapport final validé ;
- M09 ne peut pas être interprétée pour ce run ;
- M10 est impossible, car aucun Cycle B n'a été exécuté ;
- aucune comparaison appariée P1/P2 n'est recevable ;
- aucune courbe P2@3/P2@4/P2@6 ne doit être tirée de cette tentative ;
- aucune décision de déclenchement du Cycle C ne peut être prise.

## Condition minimale de reprise

La reprise doit utiliser un nouveau dossier de résultats. Avant de relancer les
230 appels, P4 doit refuser explicitement une cartographie sans clusters ou une
sortie ne respectant pas son schéma, et le statut AGNOS doit distinguer succès
technique et sortie scientifique exploitable. La tentative r1 reste conservée
comme preuve négative et ne doit pas être fusionnée avec un run ultérieur.

## Validation croisée

Rapport rédigé en lecture seule des artefacts par une instance distincte de
l'instance ayant lancé le run. Aucun appel API n'a été effectué pendant cette
analyse et aucun fichier du dossier de résultats n'a été modifié.
