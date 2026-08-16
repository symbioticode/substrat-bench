# Journal du run DeepSeek A+B r2 — 2026-08-16

## Statut

**DONNÉES PROVISOIRES — RUN ACTIF.** Ce journal décrit les artefacts présents
dans `results/deepseek-v4-flash-ab-20260816-r2`. Les nombres peuvent évoluer
jusqu'à l'événement terminal du runner. Aucune conclusion Huang, A contre B ou
inter-pipeline n'est autorisée avant 230 lignes de ledger, les métriques finales,
`summary.csv` et un événement AGNOS terminal cohérent.

## Snapshot 2026-08-16 01:55 America/Toronto

- progression : **32/230 appels** ;
- tokens entrants : **555 442** ;
- tokens sortants : **97 732** ;
- coût estimé conservateur cumulé : **0,10512684 USD** ;
- Cycle A, répétition 0 : complète, 23/23 appels ;
- Cycle A, répétition 1 : en cours, P0 et P1 terminés, P2 en cours avec 2/6
  appels inscrits ;
- processus du runner présent ;
- aucun événement AGNOS d'erreur dans les 16 événements présents ;
- dernier événement AGNOS : démarrage de P2 pour `cycle_A/repetition_1` ;
- aucun état terminal du runner.

### Répétition A0 — complète, résultats encore provisoires

| Pipeline | Appels | Sortie rapportée | État AGNOS |
|---|---:|---|---|
| P0 | 1 | 32 assertions | succès technique |
| P1 | 6 | 28 assertions finales, 46 clusters au total | succès technique |
| P2 | 6 | 29 assertions finales pour la vue native rapportée | succès technique |
| P3 | 4 | 17 assertions finales, 0 zone de non-convergence | succès technique |
| P4 | 6 | cartographes : 9 et 4 clusters ; noyau : 1 assertion finale ; 0 zone de non-convergence | succès technique |

La sortie P4 n'est pas vide, contrairement à la tentative r1 invalidée : les
deux fichiers cartographes contiennent respectivement 9 et 4 clusters et le
noyau contient une assertion finale. Ce constat valide seulement le passage du
gate mécanique pour A0 ; il ne mesure ni la justesse ni le rappel de P4.

### Répétition A1 — partielle

Au snapshot :

- P0 : 1 appel terminé ;
- P1 : 6 appels terminés ;
- P2 : 2 appels inscrits sur 6 ;
- P3 et P4 : non commencés.

Aucun `cycle_summary.json` complet n'existe encore pour A1. Aucun nombre de
sortie final n'est donc rapporté pour cette répétition.

## Méthode de mise à jour

Chaque snapshot est calculé directement depuis `inference_ledger.jsonl`, les
`cycle_summary.json`, les sorties P4 et `agnos_events.jsonl`. Les répétitions
partielles restent explicitement séparées des répétitions complètes. Les gates
DeepSeek antérieurs et la tentative r1 invalidée ne sont jamais additionnés aux
coûts ou résultats de r2.

## Snapshot 2026-08-16 01:59 America/Toronto

**DONNÉES PROVISOIRES — RUN ACTIF.**

- progression : **49/230 appels** ;
- tokens entrants : **769 280** ;
- tokens sortants : **146 236** ;
- coût estimé conservateur cumulé : **0,14864528 USD** ;
- A0 et A1 complètes ;
- A2 en cours : P0 terminé et 2/6 appels P1 inscrits ;
- aucune erreur AGNOS observée.

### Répétition A1 — complète, résultats encore provisoires

| Pipeline | Appels | Sortie rapportée | État AGNOS |
|---|---:|---|---|
| P0 | 1 | 32 assertions | succès technique |
| P1 | 6 | 34 assertions finales, 39 clusters au total | succès technique |
| P2 | 6 | 32 assertions finales pour la vue native rapportée | succès technique |
| P3 | 4 | 15 assertions finales, 0 zone de non-convergence | succès technique |
| P4 | 6 | cartographes : 6 et 8 clusters ; noyau : 1 assertion finale ; 0 zone de non-convergence | succès technique |

P4 franchit de nouveau le gate mécanique : ses cartographes et son noyau ne
sont pas vides. La répétition n'a pas encore de métriques finales interprétables
dans le cadre du run complet.
