# Profil AGNOS pour substrat-bench

## Rôle des traces

Le harnais émet des événements conformes au contrat AGNOS v2 afin de rendre
son exécution observable par un lecteur indépendant du fournisseur LLM.
Cette trace opérationnelle ne remplace pas :

- `inference_ledger.jsonl`, preuve détaillée de chaque réponse LLM ;
- les sorties brutes des pipelines ;
- la vérité terrain et les rapports M01–M10.

Une réussite d'exécution AGNOS ne constitue donc jamais un résultat
scientifique `stable`. Tant que l'interprétation des métriques n'est pas
rendue, `resultat` reste `indetermine`.

## Producteurs

| `agent_id` | Responsabilité |
|---|---|
| `substrat-runner` | début et fin du run complet |
| `substrat-p0` à `substrat-p4` | début, réussite ou erreur d'un pipeline |

## Champs supplémentaires

AGNOS tolère les champs supplémentaires. Le profil utilise les champs
suivants sans les rendre normatifs pour les autres producteurs AGNOS :

| Champ | Type | Sens |
|---|---|---|
| `run_id` | chaîne | identifiant unique ou fourni explicitement du run |
| `pipeline` | chaîne | `P0` à `P4` |
| `cycle` | chaîne | cycle expérimental `A` ou `B` |
| `repetition` | entier | répétition indexée à partir de zéro |
| `artifact_ref` | chaîne | chemin relatif vers la preuve produite |

## Mapping d'état

| Situation | `statut` | `cycle_vie` | `sante` | `resultat` |
|---|---|---|---|---|
| run ou pipeline commencé | `en_cours` | `actif` | `operationnel` | `indetermine` |
| pipeline terminé sans exception | `succès` | `termine` | `operationnel` | `indetermine` |
| exception d'exécution | `échec` | `termine` | `erreur` | `indetermine` |
| run terminé sans exception | `succès` | `termine` | `operationnel` | `indetermine` |

La valeur `resultat` ne traduit pas la détection d'un incident individuel.
Elle reste indéterminée afin de ne pas confondre santé technique et verdict
scientifique, distinction centrale du contrat AGNOS v2.

## Emplacement et lecture

Par défaut, le flux est écrit dans `<output>/agnos_events.jsonl`. Il peut être
lu directement par le lecteur de référence AGNOS :

```bash
python /chemin/vers/AGNOS/src/agnos_dashboard.py \
  --events-file results/<run>/agnos_events.jsonl
```

