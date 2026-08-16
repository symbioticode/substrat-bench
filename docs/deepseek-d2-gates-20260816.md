# Adaptation D2 DeepSeek — journal des gates du 2026-08-16

## Verdict

L'adaptateur `deepseek-v4-flash` en mode non-thinking est fonctionnel. Le run
scientifique A+B complet n'a pas été exécuté : une première tentative a été
interrompue après six appels dès qu'une non-conformité de capacité a été
observée. Les artefacts de cette tentative portent localement la mention
`INVALID_RUN.md` et sont exclus de toute analyse.

À la demande d'Andrei, aucun nouvel appel n'est lancé après le gate P3 afin de
documenter l'état avant une éventuelle limitation de débit.

## Configuration préenregistrée

- Provider : API officielle DeepSeek OpenAI-compatible,
  `https://api.deepseek.com`.
- Modèle : `deepseek-v4-flash`.
- Thinking : désactivé explicitement.
- Température : `0.6`.
- Seed demandé : conservé dans le ledger; seed effectif `null`, car l'API
  DeepSeek ne garantit pas ce paramètre.
- Capacité : 32 assertions retenues mécaniquement par réponse.
- Plafond : 4 000 tokens sortants, identique pour tous les pipelines.
- Seuil D4 : `0.36`, `all-MiniLM-L6-v2`, sans fallback lexical.
- Secret : chargé depuis `/home/andrei/Projects/61_AGORA/.env`; jamais copié
  dans le dépôt ni dans les artefacts inspectés.

Tarifs de référence consultés le 2026-08-16 : 0.14 USD/M tokens entrants en
cache miss et 0.28 USD/M tokens sortants. Les prix sont externes et peuvent
changer : voir la [documentation officielle DeepSeek](https://api-docs.deepseek.com/quick_start/pricing).

## Preuves d'exécution

| Gate | Appels | Tokens entrée | Tokens sortie | Coût conservateur USD | Verdict |
|---|---:|---:|---:|---:|---|
| Smoke 2 000 sans capacité mécanique | 1 | 13 106 | 2 000 | 0.00239 | NON — troncature |
| Smoke 4 000 sans capacité mécanique | 1 | 13 106 | 4 000 | 0.00295 | NON — troncature |
| Smoke 8 000, parseur ligne-à-ligne | 1 | 13 106 | 8 000 | 0.00407 | NON — JSON indenté non reconnu |
| Smoke final P0, capacité 32 | 1 | 13 128 | 1 759 | 0.00233 | OUI — 32 assertions, métriques D4 |
| Première tentative A+B | 6 | 102 945 | 11 506 | 0.01763 | INVALIDÉE et interrompue |
| Gate P1 complet | 6 | 142 107 | 19 689 | 0.02541 | OUI après correction du chargeur M09 |
| Gate intégral Cycle A | 20 | 300 743 | 57 094 | 0.05809 | NON global — P3 seul en erreur; P0/P1/P2/P4 verts |
| Gate P3 final | 4 | 54 531 | 15 703 | 0.01203 | OUI — 3 parseurs + arbitre + métriques |
| **Total de validation** | **40** | **652 772** | **119 751** | **0.12492** | Aucun résultat scientifique déclaré |

Le coût est recalculé en supposant tous les tokens entrants en cache miss; il
est donc conservateur. Aucun code HTTP de limitation de débit n'a été observé.

## Défauts découverts et corrections

1. DeepSeek peut indenter un objet JSON sur plusieurs lignes ou envelopper une
   liste sous `assertions`. Le parseur extrait désormais les objets successifs,
   aplatit cette enveloppe et ignore un objet invalide sans perdre les suivants.
2. Une limite écrite dans le prompt n'est pas une garantie. La capacité de 32
   est maintenant appliquée mécaniquement dans les parseurs et dans M09.
3. M09 supposait encore « une ligne = un JSON ». Son chargeur utilise désormais
   le même contrat robuste que les pipelines.
4. P3 arrêtait toute la réponse au premier objet incomplet. Il poursuit désormais
   avec les objets valides suivants, comme P0/P1/P2/P4.
5. Le Python système ne fournissait pas le backend D4 complet. Les gates réels
   ont utilisé l'environnement isolé avec `sentence-transformers` et les
   bibliothèques Nix requises; aucun fallback lexical n'a été autorisé.

## État exact avant A+B

- Tests locaux : 25/25 après documentation, confirmés par la relecture
  indépendante OpenCode.
- P0 réel : vert.
- P1 réel, deux rounds avec contact : vert.
- P2 réel, six lecteurs et vues 3/4/6 : vert dans le gate intégral.
- P3 réel, trois parseurs + arbitre : vert après correction.
- P4 réel, trois parseurs + deux cartographes + noyau : vert dans le gate intégral.
- A+B complet : non exécuté; aucune conclusion Huang/substrat n'est autorisée.

Validation croisée : `MERGE OUI`, OpenCode (`opencode_v03_audit`), 2026-08-16.

## Reprise recommandée

Créer un nouveau dossier de résultats, ne jamais reprendre le dossier invalidé,
et lancer les 230 appels avec journalisation persistante. Surveiller après chaque
répétition : nombre de lignes ledger, erreurs AGNOS, coût cumulé et réponses
HTTP 429. En cas de limitation, suspendre puis reprendre par répétition dans un
nouveau run explicitement relié; ne pas fusionner silencieusement deux ledgers.
