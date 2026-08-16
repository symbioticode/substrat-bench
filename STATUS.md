# STATUS.md — État du chantier (source de vérité)

## Sprint courant : préparation v0.3.0
## Statut : HARNAIS_MOCK_VALIDÉ — EXPÉRIENCE_RÉELLE_BLOQUÉE
## Version : v0.3.0
## Date MAJ : 2026-08-16

### Blocage Sprint 0 (décisions D1-D4 §6 protocole)
| Décision | Statut | Détail |
|----------|--------|--------|
| D1 Corpus source | ❌ BLOQUANT | Choisir session TI-360 vs LocalContext vs synthétique |
| D2 Modèle unique + budget | ❌ BLOQUANT | Claude-3.5-Sonnet / GPT-4o / Local — clés API + budget |
| D3 Traçabilité P4 Option B | ✅ ADOPTÉ PROVISOIRE | DEC-006, niveau fil round 2 |
| D4 Seuil similarité | ⏳ Sprint 1 | Calibrer sur échantillon manuel 50 paires |

### Progression BR (brainstorm/)
| BR | Sujet | Statut | Sprint cible |
|----|-------|--------|--------------|
| BR-001 | Anti-biais substrat | PROPOSÉ | 0 |
| BR-002 | Isolation réelle implémentation | PROPOSÉ | 1 |
| BR-003 | Modèle unique D2 | PROPOSÉ | 0 (BLOQUANT) |
| BR-004 | Corpus source D1 | PROPOSÉ | 0 (BLOQUANT) |
| BR-005 | Traçabilité P4 Option B | PROPOSÉ | 0 |
| BR-006 | Seuil similarité D4 | PROPOSÉ | 1 |
| BR-007 | Dawid-Skene Crowd-Kit vs custom | PROPOSÉ | 3 |
| BR-008 | Schéma sortie DiAML vs custom | PROPOSÉ | 3 |
| BR-009 | M06/M07 ChatEval vs humain | PROPOSÉ | 4 |
| BR-010 | Seuils pivot §0 | **ADOPTÉ** | 0 (figé R-PIVOT-01) |
| BR-011 | Harnais contrôle Huang v0.3.0 | **ADOPTÉ** | préparation v0.3.0 |

### État du harnais v0.3.0

- P1 = débat synchronisé, 3 instances × 2 rounds, contact round 2 testé.
- P2 = six lectures indépendantes réutilisées par P2@3/P2@4/P2@6.
- Registre d'inférence : exactement 23 réponses par répétition complète.
- M05 vectorielle, M09/M10 et comparaisons Question 0 générées.
- Gate mock A/B : 46/46 lignes ; suite dédiée : 9/9 tests.
- Observabilité AGNOS v2 : état du runner et de P0–P4, sans remplacement du
  registre scientifique (`docs/agnos-research-profile.md`).
- Les fichiers corpus et vérité terrain suivis sur `main` sont vides. Le contenu
  non commité de l'ancien worktree n'est pas intégré implicitement.

### Prochaine action requise
**ARBITRE_FINAL doit résoudre D1, D2 et valider D4**, puis intégrer un
corpus/vérité terrain revus avant tout run LLM réel. Le harnais mock ne vaut
pas résultat expérimental.

### Commandes de vérification
```bash
# Environnement
nix-shell          # ou: pip install -r requirements.txt

# Corpus (nécessite D1 résolu)
python corpus/generate_corpus.py

# Test isolation (Sprint 1)
pytest pipelines/common/isolation.py::test_isolation_assertion -v
pytest pipelines/common/isolation.py::test_debate_context_injection -v

# Expérience complète (après Sprint 3)
python run_experiment.py --cycles 5 --personas both --provider mock \
  --corpus /chemin/vers/corpus_valide.json --output results/mock-gate
```

### Gates Sprint (GNG-PAPER adapté ETAU/SECS)
| Sprint | Seuil minimum | Dimensions évaluées |
|--------|---------------|---------------------|
| 1 (P0,P1) | ≥ 60 | Solidité expé + Reproductibilité |
| 2 (P2) | ≥ 60 | Solidité expé + Reproductibilité |
| 3 (P3,P4) | ≥ 65 | Rigueur théorique isolation + traçabilité |
| 4 (Métriques) | ≥ 70 | Toutes dimensions |
| 5 (Clôture) | ≥ 80 | GO pour passation Analyste |

### Seuils pivot figés (BR-010, R-PIVOT-01)
- **Recall** : différence ≥ 10pp (p<0.05 McNemar)
- **Precision** : différence ≥ 10pp (p<0.05)
- **Cost** : P1 ≤ 0.7 × P2
- **P3 vs P4** : |Δ| < 5pp sur Recall ET Precision → P3 suffit
- **Significativité** : IQR sur 5 cycles < 30% médiane, sinon N=10
