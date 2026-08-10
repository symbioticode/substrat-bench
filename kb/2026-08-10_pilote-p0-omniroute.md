# Pilote P0 réel via Omniroute — deux LLM, disponibilité inter-provider bloquée

**Date UTC :** 2026-08-10 02:43–02:46
**Branche :** `codex/omniroute-autonome-20260810`

## Question testée

Le plancher P0 produit-il une lecture stable du petit corpus incidenté lorsque
le même protocole est répété par deux LLM accessibles à coût nul via
Omniroute ? Peut-on réellement obtenir deux providers distincts aujourd'hui ?

## Dispositif

- corpus figé de 12 tours, cinq zones attendues : contradiction, dérive,
  affirmation non étayée, lacune silencieuse, ambiguïté genuine;
- P0 existant réutilisé sans changement de prompt;
- Mistral Small et Magistral Small, température 0, cinq répétitions chacun;
- dix appels répartis sur 3 min 02 s, cache/mémoire désactivés;
- manifeste et sorties brutes conservés sous `results/omniroute_p0_long/`.

Il s'agit d'un **pilote P0**, et non du Cycle C normatif. Le protocole v0.2.2
réserve Cycle C à la répétition complète P0–P4, personas actifs, après mesure
valide des Cycles A/B et déclenchement de sa règle quantitative.

## Résultats reproductibles

| LLM demandé | Succès | Provider observé | Sorties distinctes | Assertions/run | Médiane |
|---|---:|---|---:|---:|---:|
| Mistral Small | 5/5 | mistral | 1/5 | 12 | 5,868 s |
| Magistral Small | 5/5 | mistral | 2/5 | 12 | 5,338 s |

- cache : `MISS` 10/10;
- coût déclaré par Omniroute : `$0.0000000000` 10/10;
- tokens déclarés : 8 720 entrée, 6 418 sortie;
- toutes les sorties contiennent les 12 `source_ref` attendues.

La stabilité textuelle est très forte, mais la qualité épistémique plafonne :
les deux LLM reformulent chaque tour comme une assertion. Ils signalent la
dérive de date et l'absence d'étude, mais ne nomment pas explicitement la
lacune paiement ni l'ambiguïté des deux options. La correction 10→15 M€ est
classée `Correct`, sans état de conflit `B`. Cette convergence constitue un
signal de **miss corrélé P0**, pas une preuve que les incidents sont absents.
Ce diagnostic est qualitatif : il ne doit pas être publié comme M09 avant le
matching normatif et les Cycles A/B.

## Disponibilité du second provider

| Provider/modèle sondé sur le corpus | Verdict réel |
|---|---|
| Groq Llama 3.3 70B | HTTP 403 Cloudflare Error 1010 |
| Cerebras GPT-OSS 120B | HTTP 403 Cloudflare Error 1010 |
| OC Big Pickle | HTTP 403, quota insuffisant |
| DDGW GPT-5.4 Nano | HTTP 418, challenge anti-abus |
| Felo Chat | HTTP 200 à coût nul, mais contenu invalide limité à `"}` |
| Pepper | HTTP 502 `fetch failed` |

Verdict : deux LLM fonctionnent, mais ils passent tous deux par Mistral. Le
critère « deux providers » n'est **pas** satisfait. Les échecs sont conservés
comme résultat de disponibilité et non requalifiés en indépendance.

## Dette découverte et réparée sur la branche

`origin/main` ne pouvait pas importer les pipelines : le module personas
référencé par le commit courant n'était pas versionné et `schemas.py` avait un
ordre de champs dataclass invalide. Le module minimal conforme au protocole et
les correctifs de schéma ont été ajoutés. `shell.nix` utilisait en outre le nom
Nix obsolète `pytorch`; il est remplacé par `torch`.

Le shell complet reste lourd (pile Transformers). Le pilote Omniroute est donc
volontairement stdlib-only; simplifier le shell global exige une décision
séparée car P1/P2 utilisent les embeddings locaux.

## Suite recommandée

1. Restaurer au moins un second provider Omniroute capable du corpus complet.
2. Versionner et valider un corpus/ground truth normatif de ≥24 incidents.
3. Exécuter cinq Cycles A et cinq Cycles B sur un modèle unique.
4. Calculer M09/M10; Andrei constate ensuite si la règle Cycle C est déclenchée.
5. Seulement alors, exécuter Cycle C avec le second provider restauré.
