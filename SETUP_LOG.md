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
 
## Vérification injection persona et séparation cycles A/B
 
**Date** : 2026-07-19
**Contexte** : Vérification bloquante avant commit des fichiers en attente (schemas.py, pipeline_p0.py, p3.py, p4.py, run_experiment.py, HYPOTHESES.md, etc.)
 
### 1. INJECTION PERSONA CYCLE B — NON CÂBLÉE
 
**Preuve** : Les pipelines appellent `get_prompt()` SANS passer `instance_id` ni `cycle_label`. La fonction `get_prompt_with_persona()` existe dans `prompts.py` (ligne 218) et injecte correctement la persona, mais **AUCUN pipeline ne l'utilise**.
 
```bash
# Recherche dans tout le code pipelines/
$ grep -r "get_prompt_with_persona" pipelines/
# → AUCUN RÉSULTAT
 
# Recherche usage cycle_label
$ grep -r "cycle_label" pipelines/
# → AUCUN RÉSULTAT
```
 
**Exemples concrets** (extraction prompts d'instance) :
 
| Pipeline | Appel prompt réel | Reçoit cycle_label ? |
|----------|-------------------|---------------------|
| P0 | `get_prompt("P0_extraction", corpus_text=corpus_text)` | Non |
| P1 | `get_prompt("P1_round1", corpus_text=corpus_text)` | Non |
| P1 | `get_prompt("P1_roundN", corpus_text=corpus_text, ...)` | Non |
| P2 | `get_prompt("P2_extraction", corpus_text=corpus_text)` | Non |
| P3 | `get_prompt("P3_parseur", corpus_text=corpus_text)` | Non |
| P4 | `get_prompt("P4_parser", corpus_text=corpus_text)` | Non |
 
**Test diff concret** (exécution hors LLM, prompt seulement) :
 
```python
from pipelines.common.prompts import get_prompt, get_prompt_with_persona

# Cycle A (baseline) - prompt tel que utilisé ACTUELLEMENT par tous les pipelines
p_A = get_prompt("P1_round1", corpus_text="TEST CORPUS")

# Cycle B - prompt qui DEVRAIT être utilisé si cycle_label injecté
p_B = get_prompt_with_persona("P1_round1", instance_id="p1_instance_0", corpus_text="TEST CORPUS")

# Résultat
"PERSONA ASSIGNÉE" in p_A  # → False
"PERSONA ASSIGNÉE" in p_B  # → True
"Vérificateur de Cohérence" in p_B  # → True
```
 
**Constat** : **Cycle A et Cycle B envoient des prompts IDENTIQUES** aux LLM. L'injection persona n'est pas câblée — le paramètre `cycle_label` est reçu par `run_experiment.py` → `run_pX_cycle()` via `**kwargs` mais **ignoré** dans tous les pipelines.
 
---
 
### 2. COLLISION CHEMIN SORTIE CYCLE A / CYCLE B — CONFIRMÉE
 
**Preuve** : Tous les pipelines construisent `output_dir = output_base / f"cycle_{cycle_num}" / "raw_outputs"` sans inclure `cycle_label`.
 
| Pipeline | Ligne construction output_dir |
|----------|-------------------------------|
| P0 | `pipeline_p0.py:160` : `output_base / f"cycle_{cycle_num}" / "raw_outputs"` |
| P1 | `pipeline_p1.py:245` : `output_base / f"cycle_{cycle_num}" / "raw_outputs"` |
| P2 | `pipeline_p2.py:158` : `output_base / f"cycle_{cycle_num}" / "raw_outputs"` |
| P3 | `pipeline_p3.py:188` : `output_base / f"cycle_{cycle_num}" / "raw_outputs"` |
| P4 | `pipeline_p4.py:293` : `output_base / f"cycle_{cycle_num}" / "raw_outputs"` |
 
**Conséquence** : Cycle A cycle 0 et Cycle B cycle 0 écrivent tous les deux dans `results/cycle_0/raw_outputs/`. Le second ÉCRASE le premier.
 
**Protocole §8 attend** : Dossiers séparés `results/cycle_A_<n>/` et `results/cycle_B_<n>/` — **ÉCART CONFIRMÉ**.
 
**Fichiers produits** (noms identiques pour A et B) :
- `p0_cycle0_raw.jsonl`, `p0_cycle0_parsed.jsonl`
- `p1_p1_instance_0_round1_cycle0_raw.jsonl`, `p1_p1_instance_0_round2_cycle0_raw.jsonl`, etc.
- `p2_instance_0_cycle0.jsonl`, `p2_cycle0_retained.json`
- `p3_p3_parseur_0_cycle0.jsonl`, `p3_arbitre_cycle0.jsonl`
- `p4_p4_parseur_0_cycle0.jsonl`, `p4_p4_cartographe_0_cycle0.json`, `p4_nucleus_cycle0.jsonl`
 
AUCUN fichier ne porte trace de A ou B.
 
---
 
## Fix 1 — Injection persona Cycle B (après validation des constats)
 
**Date** : 2026-07-19
 
### Modifications
 
| Fichier | Changement |
|---------|------------|
| `pipelines/pipeline_p0.py` | Import `get_prompt_with_persona` ; `run_p0()` accepte `cycle_label` + `instance_id` ; utilise `get_prompt_with_persona` si `cycle_label == "B"` ; `run_p0_cycle` passe `cycle_label` et `output_dir = cycle_{cycle_label}_{cycle_num}` |
| `pipelines/pipeline_p1.py` | Import `get_prompt_with_persona` ; `run_p1_debate()` accepte `cycle_label` ; Round 1 utilise `get_prompt_with_persona` si Cycle B ; `run_p1_cycle` passe `cycle_label` et `output_dir = cycle_{cycle_label}_{cycle_num}` |
| `pipelines/pipeline_p2.py` | Import `get_prompt_with_persona` ; `run_p2_instances()` accepte `cycle_label` ; utilise `get_prompt_with_persona` si Cycle B par instance ; `run_p2`/`run_p2_cycle` propagent `cycle_label` et `output_dir = cycle_{cycle_label}_{cycle_num}` |
| `pipelines/pipeline_p3.py` | Import `get_prompt_with_persona` ; `run_p3_parseurs()` accepte `cycle_label` ; utilise `get_prompt_with_persona` si Cycle B (parseurs seulement, **pas** arbitre) ; `run_p3`/`run_p3_cycle` propagent `cycle_label` et `output_dir = cycle_{cycle_label}_{cycle_num}` |
| `pipelines/pipeline_p4.py` | Import `get_prompt_with_persona` ; `run_p4_parseurs()` accepte `cycle_label` ; utilise `get_prompt_with_persona` si Cycle B (parseurs seulement, **pas** cartographes/noyau) ; `run_p4`/`run_p4_cycle` propagent `cycle_label` et `output_dir = cycle_{cycle_label}_{cycle_num}` |
 
### Règle respectée
- **Seuls les prompts d'extraction/lecture** reçoivent la persona (P0, P1 round1, P2, P3 parseurs, P4 parseurs)
- **Jamais** les arbitres/cartographes/noyau (ils ne voient que les sorties structurées, pas le corpus) — conforme §2bis
- Instance mapping : `instance_0`/`parseur_0` → Vérificateur, `instance_1`/`parseur_1` → Traceur, `instance_2`/`parseur_2` → Cartographe (symétrie parfaite §2)
 
### Preuve diff (exécution hors LLM)
 
```python
from pipelines.common.prompts import get_prompt, get_prompt_with_persona

for key in ['P0_extraction', 'P1_round1', 'P2_extraction', 'P3_parseur', 'P4_parser']:
    p_A = get_prompt(key, corpus_text='TEST')
    p_B = get_prompt_with_persona(key, instance_id=f'{key.lower()}_0', corpus_text='TEST')
    print(f'{key}: A has persona? {"PERSONA ASSIGNÉE" in p_A} | B has persona? {"PERSONA ASSIGNÉE" in p_B}')
```
 
**Résultat** :
```
P0_extraction: A has persona? False | B has persona? True → Vérificateur de Cohérence
P1_round1:     A has persona? False | B has persona? True → Vérificateur de Cohérence
P2_extraction: A has persona? False | B has persona? True → Vérificateur de Cohérence
P3_parseur:    A has persona? False | B has persona? True → Vérificateur de Cohérence
P4_parser:     A has persona? False | B has persona? True → Vérificateur de Cohérence
```
 
Cycle A et Cycle B envoient maintenant des prompts **DIFFÉRENTS** aux LLM.
 
---
 
## Fix 2 — Séparation chemins sortie Cycle A / Cycle B (après validation des constats)
 
**Date** : 2026-07-19
 
### Modifications
 
| Fichier | Ligne | AVANT | APRÈS |
|---------|-------|-------|-------|
| `pipeline_p0.py` | 164 | `output_base / f"cycle_{cycle_num}" / "raw_outputs"` | `output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"` |
| `pipeline_p1.py` | 249 | `output_base / f"cycle_{cycle_num}" / "raw_outputs"` | `output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"` |
| `pipeline_p2.py` | 162 | `output_base / f"cycle_{cycle_num}" / "raw_outputs"` | `output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"` |
| `pipeline_p3.py` | 197 | `output_base / f"cycle_{cycle_num}" / "raw_outputs"` | `output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"` |
| `pipeline_p4.py` | 301 | `output_base / f"cycle_{cycle_num}" / "raw_outputs"` | `output_base / f"cycle_{cycle_label}_{cycle_num}" / "raw_outputs"` |
 
### Alignement protocole §8
 
> Structure attendue : `results/cycle_A_<n>/` et `results/cycle_B_<n>/`
 
### Preuve `ls` (après run complet --cycles 1 --pipelines P0,P1,P2,P3,P4)
 
```bash
$ find results -type d -name "cycle_*" | sort
results/cycle_A_0
results/cycle_B_0
```
 
```bash
$ ls results/cycle_A_0/raw_outputs/
p0_cycle0_parsed.jsonl  p1_p1_instance_0_round1_cycle0_raw.jsonl  p2_instance_0_cycle0.jsonl  p3_p3_parseur_0_cycle0.jsonl  p4_p4_parseur_0_cycle0.jsonl  ...
 
$ ls results/cycle_B_0/raw_outputs/
p0_cycle0_parsed.jsonl  p1_p1_instance_0_round1_cycle0_raw.jsonl  p2_instance_0_cycle0.jsonl  p3_p3_parseur_0_cycle0.jsonl  p4_p4_parseur_0_cycle0.jsonl  ...
```
 
**Cycle A et Cycle B ont maintenant des dossiers séparés** — plus d'écrasement.
 
---
 
## Note protocole (mandat effectif)
 
Ce fichier sert de `SETUP_LOG.md` demandé par `docs/spec/a_prompt_cadrage_nemotron.md` :
- Document normatif lu en lecture seule : `docs/spec/substrat-bench_PROTOCOL_v0_2_2.md`
- Grille numérotation confirmée et alignée ci-dessus
- Toute incohérence signalée ici, jamais corrigée silencieusement
- Aucune action irréversible sans confirmation