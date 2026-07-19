# Difficultés Techniques & Workarounds — Banc d'essai ETAU/SECS

> Journal des problèmes rencontrés lors setup/développement et solutions appliquées.

---

## 1. Environnement Nix — `numpy` invisible hors shell interactif

### Symptôme
```bash
nix-shell --pure --run "python -c 'import numpy'"  # ModuleNotFoundError
nix-shell --pure                                   # puis python -c 'import numpy'  # OK
```

### Cause
Le `shellHook` n'est exécuté que en mode interactif. En mode `--run`, l'environnement Python n'a pas les packages Nix dans `sys.path`.

### Workaround appliqué
Toujours exécuter les scripts **à l'intérieur** du nix-shell avec `cd` explicite :
```bash
nix-shell --pure --run "cd /home/andrei/.../banc-essai && python -m pipelines.pipeline_p1"
```

### Pour plus tard
Ajouter dans `shell.nix` :
```nix
shellHook = ''
  export PYTHONPATH="${pkgs.python312Packages.numpy}/lib/python3.12/site-packages:${PYTHONPATH}"
  # ... autres packages
'';
```
Ou utiliser `nix develop` (flakes) qui gère mieux l'environnement non-interactif.

---

## 2. Prompts JSON — Conflit accolades `str.format()`

### Symptôme
```
KeyError: '"text"'  # ou '"session_id"', etc.
```
Sur `template.format(corpus_text=...)` quand le template contient du JSON littéral comme `{"text": "..."}`.

### Cause
Python `str.format()` interprète **toutes** les accolades `{...}` comme des placeholders. Le JSON dans les exemples de prompts en est rempli.

### Solution
**Doubler toutes les accolades littérales** dans les templates :
```python
# AVANT (cassé)
'{"text": "...", "source_ref": {"session_id": "..."}}'

# APRÈS (fonctionne)
'{{"text": "...", "source_ref": {{"session_id": "..."}}}}'
```
Seules les vraies variables (`{corpus_text}`, `{parser_outputs}`, etc.) restent simples.

### Points d'attention
- Appliquer à **chaque** prompt contenant du JSON d'exemple
- Vérifier avec `python -m pipelines.common.prompts` (test de formatage inclus)

---

## 3. Numérotation P1/P2 inversée vs protocole v0.2.2

### Contexte
Protocole §1 : `P1 = débat`, `P2 = vote majoritaire`
Code legacy : `pipeline_p1.py = vote`, `pipeline_p2.py = débat`

### Solution appliquée
**Échange de contenu** (pas renommage fichiers — noms `pipeline_p1.py`/`pipeline_p2.py` conservés) :
- `pipeline_p1.py` ← ancien contenu `pipeline_p2.py` (débat multi-rounds)
- `pipeline_p2.py` ← ancien contenu `pipeline_p1.py` (vote majoritaire isolé)

### Fichiers modifiés
| Fichier | Changement |
|---------|------------|
| `pipelines/pipeline_p1.py` | Réécrit complet : débat + traces par round |
| `pipelines/pipeline_p2.py` | Réécrit complet : vote majoritaire isolé |
| `pipelines/common/prompts.py` | Prompts `P1_round1`, `P1_roundN`, `P2_extraction` ajoutés |
| `run_experiment.py` | Imports inchangés (noms fichiers identiques) |

### Validation
Test mock 1 cycle (5 pipelines × 2 cycles A/B) : ✅ PASS

---

## 4. Prompts manquants après renumérotation

### Symptôme
```
Prompt inconnu: P1_round1. Disponibles: [...]
Prompt inconnu: P2_extraction. Disponibles: [...]
```

### Cause
Les clés de prompts n'ont pas suivi l'échange P1/P2.

### Solution
Ajout dans `PROMPTS` dict (`pipelines/common/prompts.py`) :
- `P1_round1` — round 1 débat (ex-`P2_round1`)
- `P1_roundN` — rounds 2+ débat (ex-`P2_roundN`)
- `P2_extraction` — extraction vote majoritaire (ex-`P1_extraction`)

Mise à jour `REQUIRED_PROMPTS` et `extraction_keys` pour injection personas.

---

## 5. Package `crowdkit` introuvable sur PyPI

### Symptôme
```
ERROR: Could not find a version that satisfies the requirement crowdkit
```

### Cause
Le package s'appelle `crowd-kit` sur PyPI (tiret), pas `crowdkit`.

### Solution
```bash
pip install crowd-kit
```
Ou via Nix : `python312Packages.crowd-kit` dans `shell.nix`.

**Note** : Non bloquant pour mock tests — Dawid-Skene non utilisé sans vrai LLM.

---

## 6. Injection persona — Remplacement `{corpus_text}` post-format

### Symptôme
Persona injectée mais placeholder `{corpus_text}` non remplacé (ou remplacé deux fois).

### Cause
`get_prompt_with_persona` appelait `get_prompt(key, **kwargs)` qui formate déjà, puis tentait `replace("{corpus_text}", ...)` sur du texte déjà formaté.

### Solution
Injecter la persona **dans le template AVANT** formatage :
```python
template = PROMPTS[key]
template_with_persona = template.replace("{corpus_text}", injection + "\n{corpus_text}")
return template_with_persona.format(corpus_text=corpus_text, **kwargs)
```
Fonction `get_prompt_with_persona` corrigée signature : `corpus_text` paramètre explicite.

---

## 7. Mock client — Détection rôle par mots-clés fragiles

### État actuel
`MockLLMClient._default_response()` détecte le rôle par recherche de sous-chaînes :
- `"NOYAU"` / `"noyau"` → réponse noyau
- `"CARTOGRAPHE"` / `"cartographe"` → réponse cartographe
- `"VOUS ÊTES L'ARBITRE"` → réponse arbitre
- `"VOUS ÊTES UN PARSEUR"` → réponse parseur
- `"DÉBAT"` / `"ROUND"` → réponse extraction

### Risque
Fragile : changement prompt casse la détection. Ne gère pas personas Cycle B.

### Amélioration future
Ajouter paramètre `role` explicite à `isolated_call()` / `make_arbiter_call()` et mock basé sur rôle structuré, pas string matching.

---

## 8. Tests unitaires — Imports relatifs cassés hors nix-shell

### Symptôme
```bash
python -m pipelines.pipeline_p1  # ModuleNotFoundError: numpy
```

### Cause
Même que #1 — packages Nix non visibles hors `nix-shell --run`.

### Workaround
Toujours lancer via :
```bash
nix-shell --pure --run "cd /path/to/banc-essai && python -m pipelines.pipeline_p1"
```

---

## Résumé actions pour prochaine session

| Priorité | Action | Fichier |
|----------|--------|---------|
| 🔴 Bloquant | Décisions D1 (corpus), D2 (modèle/clé API), D3 (Option B P4) | — |
| 🟡 Sprint 0 | `generate_corpus.py` + `ground_truth.json` | `corpus/` |
| 🟡 Sprint 0 | `.env` + config provider dans `run_experiment.py` | `run_experiment.py` |
| 🟢 Sprint 1 | Calibration D4 (seuil similarité) sur 50 paires manuelles | `pipelines/common/agregation.py` |
| 🟢 Sprint 1 | Test isolation automatisé (assert messages=1) | `pipelines/common/isolation.py` |

---

*Dernière MAJ : 2026-07-19 — Session Nemotron setup initial*

---

## 9. Mock client — Collision "Cartographe" (persona Cycle B vs détection rôle)

### Symptôme
En Cycle B, le persona `instance_2` / `parseur_2` reçoit la posture **"Cartographe des Fils Ouverts"**. Le texte de la persona contient le mot "Cartographe" → le mock `MockLLMClient._default_response()` (lignes 69-70 de `run_experiment.py`) détecte `"cartographe"` en minuscules et retourne une réponse **format cartographe** (JSON objet) au lieu du **format parseur** (JSONL avec `reasoning: {steps: [...]}`).

Résultat : `KeyError: 'dialogue_act'` lors du parsing car la réponse mock n'a pas la structure attendue par `ParseurOutput.from_jsonl()`.

### Ligne exacte en cause
```python
# run_experiment.py, lignes 69-70
elif "CARTOGRAPHE" in prompt_text or "cartographe" in prompt_text.lower():
    return self._cartographe_response()  # ← Mauvais format pour parseur avec persona
```

### Cause racine
Détection du rôle par **recherche de sous-chaînes** dans le prompt complet (texte libre). Une persona peut contenir n'importe quel mot-clé (Cartographe, Arbitre, Noyau, Débat...), cassant la logique de routing du mock.

### Workaround actuel
Néant — non bloquant pour les vrais tests LLM (le vrai modèle comprend le rôle via les instructions structurelles du prompt, pas via mots-clés). Les erreurs n'apparaissent qu'avec le mock.

### Fix futur recommandé (dette technique)
Remplacer la détection par mots-clés par un **marqueur structurel explicite** :
1. Ajouter un paramètre `role: Literal["extraction", "parseur", "arbitre", "cartographe", "noyau"]` à `isolated_call()` / `make_arbiter_call()`
2. Le mock route sur ce paramètre structuré, **jamais** sur le contenu du prompt
3. Les pipelines passent le rôle explicite (ex: `role="parseur"` pour P3/P4 parseurs, `role="arbitre"` pour P3 arbitre, etc.)

**Non corrigé maintenant** — documenté pour prochaine refactorisation mock.