# Banc d'essai ETAU/SECS

Ce dépôt compare les pipelines P0–P4 du protocole
[`substrat-bench_PROTOCOL_v0_2_2.md`](docs/spec/substrat-bench_PROTOCOL_v0_2_2.md).

## Pilote Omniroute P0

Le pilote réel n'utilise que la bibliothèque standard Python et contourne
explicitement cache et mémoire Omniroute :

```bash
PYTHONPATH=. python scripts/omniroute_p0_pilot.py \
  --models mistral/mistral-small-latest,mistral/magistral-small-latest \
  --repeats 5 --interval 15 \
  --output results/omniroute_p0_long
```

Il sait lire aussi bien une réponse JSON qu'un flux SSE — Omniroute a renvoyé
du SSE même avec `stream: false` pour Groq lors du test de disponibilité.

Ce pilote est une mesure d'ingénierie P0, pas le Cycle C normatif : le Cycle C
requiert d'abord des Cycles A/B valides, toutes les pipelines, personas actifs
et un second modèle/provider disponible.

Résultat réel du 10 août 2026 :
[KB pilote P0 Omniroute](kb/2026-08-10_pilote-p0-omniroute.md).

Un second pilote a ensuite utilisé les APIs directes Anthropic et DeepSeek,
cinq répétitions chacune. DeepSeek ne signale jamais l'ambiguïté genuine et
rarement la lacune paiement; l'union inter-provider les récupère grâce à
Sonnet. Voir
[KB pilote P0 direct](kb/2026-08-10_pilote-p0-direct-inter-provider.md).

## Vérifications légères

```bash
PYTHONPATH=. pytest -q tests pipelines/common/isolation.py pipelines/pipeline_p0.py
python scripts/lab_check.py
```

`lab_check.py` conserve les gates non franchis visibles : un pilote P0 ne
résout pas rétroactivement D1–D4 ni les Cycles A/B.
