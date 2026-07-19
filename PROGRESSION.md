# PROGRESSION.md — Suivi d'avancement par sprint

## Sprint 0 — Fondations
- [ ] VARIABLES.md complété (D1-D4 résolus)
- [ ] Corpus source choisi + anonymisé (D1)
- [ ] Modèle unique + budget validé (D2)
- [ ] Traçabilité P4 Option B confirmée (D3)
- [ ] `generate_corpus.py` exécuté → corpus_test.json + ground_truth.json (24+ incidents)
- [ ] BR-001 à BR-010 statut → ADOPTÉ/RÉSOLU
- [ ] STATUS.md = "SPRINT_1_PRÊT"
- **Critère passage** : `git clone` + `pip install -r requirements.txt` + `python corpus/generate_corpus.py` fonctionne sur machine tierce

## Sprint 1 — P0 et P1 (baselines sans structure)
- [ ] `pipelines/common/isolation.py` avec assertions §2bis + test auto
- [ ] `pipelines/common/agregation.py` clustering + Dawid-Skene wrapper
- [ ] `pipelines/common/schemas.py` schémas sortie (source_ref obligatoire §1bis)
- [ ] `pipeline_p0.py` — passe unique
- [ ] `pipeline_p1.py` — vote majoritaire isolé (N=3)
- [ ] Test auto : aucun appel isolé ne reçoit >1 message (Sprint 1 critère)
- [ ] Seuil similarité D4 fixé + justifié (échantillon manuel 50 paires)
- [ ] BR-002, BR-006 → RÉSOLU
- **Critère passage** : test isolation passe, D4 documenté

## Sprint 2 — P2 (débat, contact autorisé)
- [ ] `pipeline_p2.py` — débat multi-rounds (R=2)
- [ ] Logs conservés par round (pas seulement sortie finale)
- [ ] Test auto : contexte round 2 contient littéralement sorties round 1 autres instances
- [ ] BR-003 (si non résolu Sprint 0) → vérifier exécution réelle
- **Critère passage** : test injection contexte passe

## Sprint 3 — P3 et P4 (ETAU/SECS)
- [ ] `pipeline_p3.py` — ETAU/SECS allégé (confiance binaire, traçabilité fil)
- [ ] `pipeline_p4.py` — ETAU/SECS complet (3 niveaux, Option B D3)
- [ ] Vérif lecture code : fonctions arbitrage/cartographie sans paramètre corpus_text
- [ ] Label confiance seulement sortie finale arbitre/noyau (jamais parseurs)
- [ ] BR-005, BR-007, BR-008 → RÉSOLU
- **Critère passage** : isolation structurelle vérifiée, labels confiance corrects

## Sprint 4 — Métriques
- [ ] `metrics/metrics.py` — M01-M05, M08 automatisés ; M06/M07 `required_manual_step: true`
- [ ] `metrics_report.json` + `summary.csv` par cycle
- [ ] `summary.csv` lisible par instance analyse sans traitement
- [ ] BR-009 → RÉSOLU
- **Critère passage** : métriques cohérentes sur 5 cycles, M06/M07 flaggés explicites

## Sprint 5 — Clôture et passation
- [ ] `ANALYSIS_PROTOCOL.md` : adaptation P4 (§2), valeurs D1-D4, écarts doc/code
- [ ] `PROGRESSION.md` à jour
- [ ] Dossier `results/` transmis à instance analyse (JAMAIS à agent code)
- [ ] `STATUS.md` = "ANALYSE_EN_COURS"
- **Critère passage** : tiers peut reproduire scoring sans code source