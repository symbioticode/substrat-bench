# SETUP_LOG.md — Journal d'initialisation session Nemotron

## Confirmation grille numérotation P1/P2 (§1 protocole v0.2.2)

**Date** : 2026-07-19
**Session** : Nouvelle session Nemotron sur substrat-bench (banc-essai/)

### Grille lue dans `docs/spec/substrat-bench_PROTOCOL_v0_2_2.md` (§1, §2 note) :

> **P0 = passe unique · P1 = débat multi-instances · P2 = vote majoritaire · P3 = ETAU/SECS allégé · P4 = ETAU/SECS complet**

### État AVANT correction (CONFLIT DÉTECTÉ) :

| Fichier code | Pipeline implémenté | Numérotation protocole |
|--------------|---------------------|------------------------|
| `pipelines/pipeline_p0.py` | Passe unique | **P0 ✓** (correct) |
| `pipelines/pipeline_p1.py` | **Vote majoritaire isolé** | **P2** (devrait être P2, pas P1) |
| `pipelines/pipeline_p2.py` | **Débat multi-instances** | **P1** (devrait être P1, pas P2) |
| `pipelines/pipeline_p3.py` | ETAU/SECS allégé | **P3 ✓** |
| `pipelines/pipeline_p4.py` | ETAU/SECS complet | **P4 ✓** |

**CONSTAT** : La numérotation P1/P2 est **inversée** dans le code par rapport au protocole v0.2.2. C'est exactement la "coquille de numérotation" mentionnée en §2 (note v0.2) : *"le titre v0.1 de ce sprint désignait le débat par 'P2' — coquille de numérotation par rapport à sa propre grille du §1. Grille faisant foi (§1) : le débat est P1, le vote majoritaire est P2."*

---

## Correction effectuée

### Échange de contenu (pas renommage fichiers — les noms `pipeline_p1.py` / `pipeline_p2.py` restent)

| Fichier | AVANT (contenu) | APRÈS (contenu) |
|---------|-----------------|-----------------|
| `pipelines/pipeline_p1.py` | Vote majoritaire isolé (ex-P2) | **Débat multi-instances** (ex-contenu P2) |
| `pipelines/pipeline_p2.py` | Débat multi-instances (ex-P1) | **Vote majoritaire isolé** (ex-contenu P1) |

**Détails modifications :**

1. **`pipeline_p1.py`** — Maintenant implémente P1 = DÉBAT :
   - `run_p1_debate()` : rounds 1..R, injection sorties autres instances au round N+1
   - `P1InstanceRound`, `P1InstanceTrace`, `P1Result` dataclasses
   - Validation injection contexte : `assert "SORTIES AUTRES INSTANCES" in content`
   - Sauvegarde traces complètes par round (exigence Sprint 2)

2. **`pipeline_p2.py`** — Maintenant implémente P2 = VOTE MAJORITAIRE :
   - `run_p2_instances()` : N instances isolées, même prompt
   - `aggregate_p2_vote()` : clustering + vote majoritaire (même code que P1 final)
   - Sauvegarde brute par instance + agrégée

3. **`pipelines/common/prompts.py`** — Ajout prompts manquants alignés nouvelle numérotation :
   - `P1_round1` (remplace ex-`P2_round1`)
   - `P1_roundN` (remplace ex-`P2_roundN`)
   - `P2_extraction` (remplace ex-`P1_extraction`)
   - Échappement accolades JSON dans templates (`{{...}}`) pour `.format()`

4. **Imports mis à jour** — `run_experiment.py` inchangé (imports `run_p1_cycle`, `run_p2_cycle` par nom fichier)

### État APRÈS correction (aligné protocole v0.2.2) :

| Fichier code | Pipeline implémenté | Numérotation protocole |
|--------------|---------------------|------------------------|
| `pipelines/pipeline_p0.py` | Passe unique | **P0 ✓** |
| `pipelines/pipeline_p1.py` | **Débat multi-instances** | **P1 ✓** |
| `pipelines/pipeline_p2.py` | **Vote majoritaire isolé** | **P2 ✓** |
| `pipelines/pipeline_p3.py` | ETAU/SECS allégé | **P3 ✓** |
| `pipelines/pipeline_p4.py` | ETAU/SECS complet | **P4 ✓** |

---

## Validation test mock 1 cycle

```bash
nix-shell --pure --run "cd /home/andrei/Projects/59_MONITORING/PROMPTS/ETAU-SECS-STRESS-TEST/banc-essai && python run_experiment.py --cycles 1 --provider mock --pipelines P0,P1,P2"
```

**Résultat** : ✅ **SUCCÈS** — 5 pipelines (P0, P1, P2, P3, P4) × 2 cycles (A+B) exécutés sans erreur
- P0 : 3 assertions / cycle
- P1 (débat) : 3 instances × 2 rounds, traces conservées
- P2 (vote) : 3 instances isolées, agrégation vote ≥2/3
- P3/P4 : ETAU/SECS allégé/complet, mock responses adaptées
- Métriques M01-M10 calculées, `summary.csv` généré

---

## Difficultés rencontrées & workarounds

### 1. Environnement Nix — `numpy` non trouvé dans `nix-shell` script direct

**Problème** : `python -c 'import numpy'` fonctionne dans `nix-shell` interactif mais échoue via `nix-shell --run "python ..."` (ModuleNotFoundError).

**Cause** : Le `shellHook` n'est pas exécuté dans le mode `--run` non-interactif, et le `PYTHONPATH` n'inclut pas les packages Nix.

**Workaround** : Utiliser `cd /path && python -m module` **à l'intérieur** du nix-shell :
```bash
nix-shell --pure --run "cd /home/andrei/.../banc-essai && python -m pipelines.pipeline_p1"
```
Cela force l'exécution dans l'environnement Nix avec tous les packages disponibles.

### 2. Prompts JSON — Conflit accolades `.format()`

**Problème** : Les exemples JSON dans les prompts (ex: `{"text": "..."}`) contiennent des `{}` qui entrent en conflit avec `str.format()` de Python.

**Solution** : Doubler toutes les accolades littérales dans les templates : `{{"text": "..."}}`. Seules les vraies variables (`{corpus_text}`, `{parser_outputs}`, etc.) restent simples.

### 3. Prompts manquants après renumérotation P1/P2

**Problème** : `run_experiment.py` cherchait `P1_extraction`, `P2_extraction`, `P1_round1`, etc. qui n'existaient plus après l'échange.

**Solution** : Ajoutés dans `prompts.py` avec noms alignés nouvelle grille :
- `P1_round1`, `P1_roundN` (débat)
- `P2_extraction` (vote majoritaire)
- Validation `REQUIRED_PROMPTS` mise à jour

### 4. `crowdkit` indisponible sur PyPI (package renommé)

**Problème** : `pip install crowdkit` échoue — le package s'appelle `crowd-kit` sur PyPI.

**Note** : Installé via Nix (`python312Packages.crowd-kit` à ajouter dans `shell.nix` si besoin Dawid-Skene). Pour l'instant mock tests passent sans.

---

## Prochaine unité de travail

**Sprint 0 — Fondations repo (suite)**

- [ ] `generate_corpus.py` — injection incidents + `ground_truth.json` (bloqué par D1)
- [ ] `corpus/source/corpus_source.json` — corpus réel choisi (D1)
- [ ] Variables d'env `.env` + clés API provider (D2)
- [ ] Confirmation Option B traçabilité P4 (D3)
- [ ] Seuil similarité D4 — calibration échantillon 50 paires Sprint 1

Attente décisions ARBITRE_FINAL sur D1, D2, D3 avant poursuite.

---

## Note protocole (mandat effectif)

Ce fichier sert de `SETUP_LOG.md` demandé par `docs/spec/a_prompt_cadrage_nemotron.md` :
- Document normatif lu en lecture seule : `docs/spec/substrat-bench_PROTOCOL_v0_2_2.md`
- Grille numérotation confirmée et alignée ci-dessus
- Toute incohérence signalée ici, jamais corrigée silencieusement
- Aucune action irréversible sans confirmation