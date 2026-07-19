---

## 🔴 BLOQUANT Sprint 0 — Décisions D1/D2/D3

> État temps réel des blocages vrais (pas des tâches en cours).

---

## 🔴 BLOQUANT Sprint 0 — Décisions D1/D2/D3

| ID | Décision | Statut | Requis pour | Responsable |
|----|----------|--------|-------------|-------------|
| **D1** | Corpus source | ❌ **BLOQUANT** | `generate_corpus.py` + vrais runs | ARBITRE_FINAL |
| **D2** | Modèle unique + budget | ❌ **BLOQUANT** | Vrais runs LLM | ARBITRE_FINAL |
| **D3** | Traçabilité P4 Option B | ❌ **BLOQUANT** | Sprint 3 passage | ARBITRE_FINAL |
| **D4** | Seuil similarité D4 | ⏳ Sprint 1 | Sprint 1 passage | AGENT_CODE |

> **Règle protocole §6** : *Rien en Sprint 0 ne peut commencer sans ces quatre réponses.*

### D1 — Corpus source
- **Options** : A. Session TI-360 (dérive β=N connue) / B. Brainstorming LocalContext / C. Synthétique pur
- **Critères** : Contient dérive documentée + longueur < contexte 1 appel + anonymisation si sensible

### D2 — Modèle unique + budget
- **Options** : A. Claude-3.5-Sonnet / B. GPT-4o / C. Local Llama-3.1-70B (Ollama/vLLM)
- **Budget estimé** : ~23 appels/cycle × 10 cycles (A+B) = 230 appels
- **Free tiers** : Gemini, Groq, Cerebras, Mistral, NVIDIA NIM disponibles

### D3 — Traçabilité P4 Option B
- **Options** : A. Ligne / B. Fil (défaut, round 2) / C. Assertion
- **Note** : Choix provisoire testable, ne tranche pas question définitive

---

## 🟡 BLOQUANT Sprint 1 — D4 Seuil similarité

| ID | Décision | Statut | Requis pour | Responsable |
|----|----------|--------|-------------|-------------|
| **D4** | Seuil similarité sémantique | ⏳ **Sprint 1** | Clustering assertions P1/P2 | AGENT_CODE |

- **Options** : A. 0.85 (conservateur, ada-002 legacy) / B. 0.45-0.50 (text-embedding-3, S. Anand 2024) / C. Calibré échantillon manuel 50 paires Sprint 1
- **Action** : Calibration sur 50 paires assertions humaines annotées → rapport court → figé pour tout le cycle

---

## 🟢 NON-BLOQUANT — Architecture prête

| Composant | Statut | Note |
|-----------|--------|------|
| 5 pipelines P0-P4 | ✅ Code prêt | Mock validé 1 cycle A+B |
| Isolation réelle | ✅ Code + tests | `isolated_call()`, `make_arbiter_call()` |
| Agrégation code (vote/Dawid-Skene) | ✅ | `SemanticClusterer`, `DawidSkeneAggregator` |
| Schémas sortie + source_ref | ✅ | `StructuredAssertion`, `ArbitratedAssertion` |
| Personas Cycle B | ✅ | 3 postures, injection déterministe |
| Métriques M01-M10 | ✅ Code | M09/M10 nouveaux, M06/M07 flaggés |
| Orchestrateur Cycles A+B | ✅ | `run_experiment.py --cycles N` |
| Mock client intelligent | ✅ | Détection rôle (parseur/arbitre/cartographe/noyau) |

---

## ⚠️ Points d'attention (non-bloquants mais critiques)

| Sujet | Risque | Mitigation |
|-------|--------|------------|
| **M10 non dans `metrics.py`** | Calculé côté client (`run_experiment.py`) mais pas remonté dans `metrics_report.json` | Ajouter dans `compute_metrics()` ou post-process |
| **Mock client réponses fixes** | Ne teste pas vraies capacités LLM | Vrais runs requis pour validation |
| **M06/M07 manuels** | Instance analyse séparée requise | Documenter procédure Sprint 5 |
| **Numérotation P1/P2 inversée vs doc legacy** | `etau_secs_vs_base_trivial.md` (v0.1) a numérotation différente | `ETAU_SECS_banc_essai_multisprint_v0.2.md` fait foi — noter dans `ANALYSIS_PROTOCOL.md` Sprint 5 |

---

## 🔴 Dettes techniques révélées par `lab_check.py` (2026-07-19)

| ID | Section | Problème | Impact | Sprint concerné |
|----|---------|----------|--------|-----------------|
| **DT-01** | D1-D4 | D1-D4 en attente (placeholders `EN ATTENTE`) | Impossible de lancer vrais runs | Sprint 0 |
| **DT-02** | Sprint 4 | `metrics_report.json` : M09 absent (par pipeline + agrégé + par type) | Métrique signature monosubstrat non calculée | Sprint 4 |
| **DT-03** | Sprint 4 | `summary.csv` : colonne `cycle` (A/B/C) absente | Comparaison inter-cycles impossible | Sprint 4 |
| **DT-04** | Sprint 3 | P3 : risque fuite `persona` vers arbitre (code contient "persona") | Anonymisation §2 violée si arbitre reçoit info persona | Sprint 3 |
| **DT-05** | Sprint 0 | `prompts/personas/` : dossier créé mais fichiers vides/placeholder | Personas non recopiés verbatim depuis Annexe A | Sprint 0 |
| **DT-06** | Sprint 4 | M10 (Persona Delta Recall) calculé côté client mais pas dans `metrics_report.json` | M10 invisible pour instance analyse | Sprint 4 |
| **DT-07** | Cycles A/B | Provider inconnu dans raw_results (pas de champ `provider`) | Impossible de distinguer mock vs vrai LLM a posteriori | Sprint 4 |

> **Note** : Ces 7 dettes sont de vraies découvertes (pas des tâches planifiées). Elles doivent être traitées dans les sprints correspondants avant la passation à l'instance d'analyse (Sprint 5).

---

*Dernière MAJ : 2026-07-19 — Auto-généré depuis STATUS.md + analyse code + `lab_check.py`*