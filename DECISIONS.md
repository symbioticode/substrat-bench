# DECISIONS.md — Banc d'essai ETAU/SECS : Décisions d'architecture tracées

> Toute décision technique non-triviale est tracée ici avec justification.
> Format : ID, Date, Contexte, Options, Décision, Justification, Impact.

---

## DEC-001 — Isolation réelle via code (pas prompt)
**Date** : 2026-07-19
**Contexte** : §2bis protocole exige isolation structurelle — pas "faire semblant" dans même thread.
**Options** :
- A. Assertion `len(messages)==1` + signature sans `corpus_text` pour arbitres
- B. Wrapper classe avec état privé
- C. Processus séparés (multiprocessing)
**Décision** : A
**Justification** : Vérifiable par lecture de code + test unitaire Sprint 1/2. Zéro overhead runtime.
**Impact** : `pipelines/common/isolation.py` — fonctions `isolated_call`, `make_arbiter_call`, `validate_isolation`

---

## DEC-002 — Source_ref obligatoire pour TOUS pipelines (§1bis)
**Date** : 2026-07-19
**Contexte** : Biais mesure si seul P3/P4 contraint source_ref (§1bis).
**Options** :
- A. Prompt unique avec source_ref pour P0-P4
- B. Prompts libres pour P0-P1-P2, structuré pour P3-P4
**Décision** : A
**Justification** : Égalité de matching pour M01-M03. Coût marginal négligeable.
**Impact** : `pipelines/common/prompts.py` — tous prompts incluent `source_ref` obligatoire

---

## DEC-003 — Agrégation par code (pas IA) pour P1/P2
**Date** : 2026-07-19
**Contexte** : §2 P1/P2 — agrégation vote majoritaire par code (clustering + comptage).
**Options** :
- A. Appel LLM juge pour agréger
- B. Code déterministe : clustering embeddings + seuil vote
**Décision** : B
**Justification** : Reproductibilité bit-à-bit (R-REPRO-02), pas de variabilité juge.
**Impact** : `pipelines/common/agregation.py` — `SemanticClusterer`, `majority_vote_aggregation`

---

## DEC-004 — Dawid-Skene (Crowd-Kit) pour arbitrage P3/P4
**Date** : 2026-07-19
**Contexte** : P3/P4 arbitre/cartographes assignent confiance — besoin modèle fiabilité par instance.
**Options** :
- A. Vote pondéré simple (confiance déclarée)
- B. Dawid-Skene EM (apprend matrice confusion par instance)
- C. MACE (Bayésien)
**Décision** : B (Crowd-Kit `DawidSkene`)
**Justification** : Standard éprouvé, `pip install crowdkit`, matrices confusion exploitables pour M04.
**Impact** : `pipelines/common/agregation.py` — `DawidSkeneAggregator` wrapper

---

## DEC-005 — Seuil similarité D4 à calibrer
**Date** : 2026-07-19
**Contexte** : D4 §6 — seuil cosinus pour clustering assertions. ada-002 legacy 0.85 vs nouveaux modèles ~0.45.
**Options** :
- A. 0.85 (conservateur)
- B. 0.50 (S. Anand 2024 pour text-embedding-3)
- C. Calibré Sprint 1 sur échantillon manuel 50 paires
**Décision : C** — calibration sur 50 paires annotées avant le premier run réel.
**Statut** : FIGÉ — seuil cosinus `0.36`.
**Justification** : Le code utilise `all-MiniLM-L6-v2`; reprendre un seuil publié
pour un autre modèle d'embedding serait une fausse validation. La valeur finale
Le 2026-08-16, la calibration sur 25 paires positives et 25 négatives a donné
précision `0.7667`, rappel `0.92`, F1 `0.8364` au seuil `0.36`. Modèle exact :
`sentence-transformers/all-MiniLM-L6-v2`; hash SHA-256 du jeu annoté :
`369cbee32b9f48742b2e99f064bad70c535ace5fc82cf3a63f2064814f0fd580`.
Rapport : `corpus/d4_calibration_report.json`. Aucun fallback lexical autorisé.
**Impact** : `VARIABLES.md` BLOC 6, `agregation.py` default

---

## DEC-006 — Traçabilité P4 Option B (niveau fil, round 2)
**Date** : 2026-07-19
**Contexte** : D3 §6 — choix provisoire pour testabilité.
**Options** :
- A. Niveau ligne (coût tokens élevé, traçabilité max)
- B. Niveau fil (équilibre, produit round 2 cartographes)
- C. Pas de traçabilité fine
**Décision : B** (niveau fil, défaut révisable)
**Justification** : Permet M06 testable sans explosion tokens. Ne tranche pas spéc finale.
**Impact** : BR-005, `pipeline_p4.py` cartographes produisent `trace_fil`

---

## DEC-007 — Modèle unique pour 5 pipelines (D2)
**Date** : 2026-07-19
**Contexte** : §1 protocole — contrainte non-négociable : un seul modèle.
**Options révisées le 2026-08-16** :
- A. OpenAI `gpt-4.1-mini-2025-04-14` (snapshot figé, adaptateur existant)
- B. GPT-5.6 Terra (adaptation Responses API requise)
- C. Gemini 3.6 Flash (nouvel adaptateur requis)
**Décision : A** — OpenAI `gpt-4.1-mini-2025-04-14`.
**Justification** : snapshot reproductible et compatible avec l'adaptateur du
harness. Budget : 230 réponses pour A+B; 115 supplémentaires seulement si C
est déclenché. `OPENAI_API_KEY` est absente de l'environnement au moment de la
décision; aucun run payant n'est autorisé avant disponibilité et smoke test.

---

## DEC-008 — Corpus source D1 : Session TI-360 documentée
**Date** : 2026-07-19
**Contexte** : D1 §6 — corpus réel avec dérive β=N documentée.
**Options** :
- A. Session TI-360 existante (dérive connue, longueur contrôlée)
- B. Brainstorming LocalContext (plus riche, multi-locuteurs)
- C. Synthétique pur (contrôle total, moins réaliste)
**Décision : B** — fenêtres réelles anonymisées de `session_1.md` (segments
103, 107–179, 181, 185–191) et `session_5.md` (3–18, 24–71, 74–100,
104–161, 165–179, 181–219, 221–225), segmentées en 11 tours. Les synthèses
dérivées sont exclues. Le manifeste exécutable exact est `SEGMENTS` dans
`corpus/prepare_localcontext_source.py`.
**Justification** : conversation réelle, révisions et désaccords, environ
6 900 mots avant injection, compatible avec la fenêtre du modèle D2. Sélection
confirmée par une relecture indépendante OpenCode le 2026-08-16.
Le banc est explicitement hybride : les incidents gold sont des micro-dialogues
contrôlés greffés dans deux conversations composites avec les tours réels. Il mesure la détection de classes
connues dans un contexte réaliste, mais ne permet pas d'estimer leur fréquence
naturelle ni de prétendre qu'ils sont survenus spontanément dans LocalContext.

---

## DEC-009 — M06/M07 : ChatEval panel vs Humain
**Date** : 2026-07-19
**Contexte** : BR-009 — M06 (Traceability Utility) & M07 (Closure) requièrent humain §4.
**Options** :
- A. 100% humain (protocole strict)
- B. Panel ChatEval 3 agents (FactChecker, SourceTracer, Skeptic)
- C. Hybride : ChatEval pré-filtrage + confirmation humaine
**Décision** : ⏳ **EN ATTENTE Sprint 4** — BR-009
**Justification** : Fidélité §4 vs faisabilité 5 cycles automatisés.

---

## DEC-010 — Seuils pivot figés R-PIVOT-01 (BR-010)
**Date** : 2026-07-19
**Contexte** : §0 règle de pivot — seuils numériques AVANT résultats.
**Décision** : **ADOPTÉ** — valeurs dans BR-010 immuables
- Recall diff ≥ 10pp (p<0.05 McNemar)
- Precision diff ≥ 10pp
- Cost P1 ≤ 0.7×P2
- P3 vs P4 diff < 5pp → P3 suffit
**Impact** : Non-négociable post-résultats. Guide décision finale ARBITRE_FINAL.

---

## Template pour nouvelles décisions

```markdown
## DEC-XXX — Titre court
**Date** : YYYY-MM-DD
**Contexte** : [Référence protocole §X / BR-YYY]
**Options** :
- A. [Option A]
- B. [Option B]
**Décision** : [A/B/C/⏳ EN ATTENTE]
**Justification** : [Raison technique/stratégique]
**Impact** : [Fichiers/moduls concernés, BR mis à jour]
```
