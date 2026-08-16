# substrat-bench

Un banc d'essai contrôlé pour mesurer ce que la diversité apporte réellement
à un système multi-agents fondé sur des modèles de langage.

## La question

> Plusieurs agents reposant sur un même modèle voient-ils réellement plus
> qu'un seul agent, ou leurs erreurs restent-elles corrélées au point qu'un
> second substrat — un autre modèle ou provider — soit nécessaire ?

La trace la plus ancienne conservée dans le projet formule un sous-problème
plus précis : **« les personas suffisent-elles à limiter la casse du
monosubstrat ? »** Le protocole le transforme en question mesurable :

> Des instances d'un même modèle, dotées de postures épistémiques distinctes,
> ratent-elles moins souvent toutes ensemble le même incident que des
> instances au prompt uniforme ?

La littérature donne une raison sérieuse de poser la question, mais pas de
réponse universelle à appliquer sans mesure. Des agents homogènes peuvent
produire des réponses fortement corrélées et des rendements décroissants ;
des modèles hétérogènes peuvent apporter des erreurs et des biais inductifs
complémentaires. L'effet dépend toutefois de la tâche, des modèles et de la
forme de coordination.

`substrat-bench` sert à vérifier ce mécanisme sur un corpus fermé avec vérité
terrain, plutôt qu'à déduire la qualité d'un ensemble du seul nombre de ses
agents.

## Ce que le banc compare

Le protocole croise trois facteurs qui doivent rester distincts :

1. **architecture** — passe unique, débat, vote isolé, ETAU/SECS allégé ou
   complet ;
2. **diversité de lecture** — prompts uniformes ou personas épistémiques ;
3. **diversité de substrat** — même modèle ou second modèle/provider lorsque
   la règle de déclenchement l'exige.

| Pipeline | Configuration |
|---|---|
| P0 | Une instance, plancher de référence |
| P1 | Débat multi-instances, contact autorisé |
| P2 | Instances isolées, agrégation par vote |
| P3 | ETAU/SECS allégé : sorties contraintes et arbitrage par cohérence |
| P4 | ETAU/SECS complet : parseurs, cartographes et noyau |

Le plan expérimental comporte :

- **Cycle A** : plusieurs instances du même modèle, prompts uniformes ;
- **Cycle B** : même modèle et mêmes pipelines, avec postures de lecture
  distinctes ;
- **Cycle C** : second modèle/provider, seulement si la règle quantitative
  fixée avant les résultats est déclenchée.

Deux métriques portent directement la question du dépôt :

- **M09 — Correlated Miss Rate** : part des incidents connus ratés par toutes
  les instances ;
- **M10 — Persona Delta Recall** : variation du rappel entre les Cycles B et
  A.

La spécification normative complète est
[`docs/spec/substrat-bench_PROTOCOL_v0_2_2.md`](docs/spec/substrat-bench_PROTOCOL_v0_2_2.md).

## Ce que le banc ne permet pas de conclure

- Une convergence entre agents n'est pas, à elle seule, une confirmation :
  elle peut être un échec corrélé.
- Un gain obtenu sur un corpus fermé ne démontre pas une supériorité générale
  en exploration ouverte.
- Des personas diversifient les angles de lecture ; ils ne créent pas un
  second corpus d'entraînement.
- Un pilote P0 inter-provider ne remplace ni les Cycles A/B complets, ni M09,
  ni le Cycle C normatif.
- Un résultat négatif doit rester visible : si un vote simple égale une
  architecture plus coûteuse, le protocole prévoit de le rapporter et de
  pivoter.

## État des preuves

Le dépôt contient un harnais reproductible, un corpus incidenté, une vérité
terrain séparée des agents lecteurs et des exécutions mock. La branche
[`codex/omniroute-autonome-20260810`](https://github.com/symbioticode/substrat-bench/tree/codex/omniroute-autonome-20260810)
ajoute deux pilotes P0 réels :

- deux modèles servis par un même provider ont produit des omissions
  communes sur le petit corpus pilote ;
- un essai direct Anthropic/DeepSeek a montré des détections complémentaires,
  l'union inter-provider récupérant deux zones que DeepSeek omettait souvent
  ou toujours sur cinq répétitions.

Ces observations justifient l'expérience ; elles ne constituent pas encore
sa conclusion normative. Le protocole complet exige toujours un corpus et
une vérité terrain validés, les Cycles A/B, le calcul M09/M10 et, si le seuil
le déclenche, le Cycle C.

## Démarrage

Avec Nix :

```bash
nix-shell
python run_experiment.py --cycles 1 --provider mock
```

Avec un environnement Python existant :

```bash
python -m pip install -r requirements.txt
python run_experiment.py --cycles 1 --provider mock
```

Vérifications légères :

```bash
PYTHONPATH=. pytest -q
python scripts/lab_check.py
```

Consulter avant toute expérience réelle :

- [`STATUS.md`](STATUS.md) — état courant et blocages ;
- [`VARIABLES.md`](VARIABLES.md) — décisions expérimentales ;
- [`HYPOTHESES.md`](HYPOTHESES.md) — hypothèses et résultats, y compris
  négatifs ;
- [`DECISIONS.md`](DECISIONS.md) — décisions d'architecture ;
- [`SETUP_LOG.md`](SETUP_LOG.md) — trace d'installation et d'exécution.

## Repères scientifiques

Ces travaux motivent la mesure de diversité sans servir de résultat de
substitution au banc :

- Yang et al., *Understanding Agent Scaling in LLM-Based Multi-Agent Systems
  via Diversity* (2026) — comparaison d'ensembles homogènes et hétérogènes :
  <https://arxiv.org/abs/2602.03794>
- Yuan et al., *Do Mixed-Vendor Multi-Agent LLMs Improve Clinical
  Diagnosis?* (HeaLing 2026) — comparaison single-LLM, single-vendor et
  mixed-vendor sur un domaine clinique :
  <https://aclanthology.org/2026.healing-1.1/>
- Chen et al., *Diversity Collapse in Multi-Agent LLM Systems* (ACL 2026) —
  effets de la structure d'interaction sur la diversité collective :
  <https://aclanthology.org/2026.findings-acl.13/>

## Origine

Le banc est né d'un besoin de tester empiriquement une question à réponse
académique : **la multiplicité d'agents ne garantit pas l'indépendance de
leurs erreurs**. Son objet est de rendre cette proposition falsifiable dans
un dispositif local, inspectable et reproductible.
