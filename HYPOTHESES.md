# Registre des Hypothèses Testées — Banc d'essai ETAU/SECS

> **Format inspiré Agora (61_AGORA)** — Une ligne par exécution pipeline×cycle.
> Synthèse Gate S1→S5 selon seuils BR-010 (R-PIVOT-01).

---

## Résultats Bruts — Cycle par Cycle

### Cycle 0
| Pipeline | Assertions | Recall | Precision | FSR | Cost/Det | Fort% | NonConv | Status |
|----------|------------|--------|-----------|-----|----------|-------|---------|--------|
| P0 | — | — | — | — | — | — | — | ⏳ En attente |
| P1 | — | — | — | — | — | — | — | ⏳ En attente |
| P2 | — | — | — | — | — | — | — | ⏳ En attente |
| P3 | — | — | — | — | — | — | — | ⏳ En attente |
| P4 | — | — | — | — | — | — | — | ⏳ En attente |

### Cycle 1
| Pipeline | Assertions | Recall | Precision | FSR | Cost/Det | Fort% | NonConv | Status |
|----------|------------|--------|-----------|-----|----------|-------|---------|--------|
| P0 | — | — | — | — | — | — | — | ⏳ En attente |
| P1 | — | — | — | — | — | — | — | ⏳ En attente |
| P2 | — | — | — | — | — | — | — | ⏳ En attente |
| P3 | — | — | — | — | — | — | — | ⏳ En attente |
| P4 | — | — | — | — | — | — | — | ⏳ En attente |

### Cycle 2
| Pipeline | Assertions | Recall | Precision | FSR | Cost/Det | Fort% | NonConv | Status |
|----------|------------|--------|-----------|-----|----------|-------|---------|--------|
| P0 | — | — | — | — | — | — | — | ⏳ En attente |
| P1 | — | — | — | — | — | — | — | ⏳ En attente |
| P2 | — | — | — | — | — | — | — | ⏳ En attente |
| P3 | — | — | — | — | — | — | — | ⏳ En attente |
| P4 | — | — | — | — | — | — | — | ⏳ En attente |

### Cycle 3
| Pipeline | Assertions | Recall | Precision | FSR | Cost/Det | Fort% | NonConv | Status |
|----------|------------|--------|-----------|-----|----------|-------|---------|--------|
| P0 | — | — | — | — | — | — | — | ⏳ En attente |
| P1 | — | — | — | — | — | — | — | ⏳ En attente |
| P2 | — | — | — | — | — | — | — | ⏳ En attente |
| P3 | — | — | — | — | — | — | — | ⏳ En attente |
| P4 | — | — | — | — | — | — | — | ⏳ En attente |

### Cycle 4
| Pipeline | Assertions | Recall | Precision | FSR | Cost/Det | Fort% | NonConv | Status |
|----------|------------|--------|-----------|-----|----------|-------|---------|--------|
| P0 | — | — | — | — | — | — | — | ⏳ En attente |
| P1 | — | — | — | — | — | — | — | ⏳ En attente |
| P2 | — | — | — | — | — | — | — | ⏳ En attente |
| P3 | — | — | — | — | — | — | — | ⏳ En attente |
| P4 | — | — | — | — | — | — | — | ⏳ En attente |

---

## Synthèse Gates (R-PIVOT-01)

### Gate Sprint 1 — Baselines (P0, P1)
| Critère | Seuil | P0 | P1 | Status |
|---------|-------|-----|-----|--------|
| Isolation test | 100% pass | — | — | ⏳ |
| D4 fixé + justifié | échantillon 50 paires | — | — | ⏳ |
| GNG ≥ 60 | — | — | — | ⏳ |

### Gate Sprint 2 — Débat (P2)
| Critère | Seuil | Status |
|---------|-------|--------|
| Injection contexte R2 | test auto pass | ⏳ |
| GNG ≥ 60 | — | ⏳ |

### Gate Sprint 3 — ETAU/SECS (P3, P4)
| Critère | Seuil | P3 | P4 | Status |
|---------|-------|-----|-----|--------|
| Isolation structurelle | lecture code | — | — | ⏳ |
| Labels confiance (jamais parseur) | lecture code | — | — | ⏳ |
| D3 (Option B) implémentée | traçabilité fil round 2 | — | — | ⏳ |
| GNG ≥ 65 | — | — | — | ⏳ |

### Gate Sprint 4 — Métriques (M01-M08)
| Critère | Seuil | Status |
|---------|-------|--------|
| M01-M05 automatisés | run_all_metrics OK | ⏳ |
| M06/M07 flaggés | required_manual_step=true | ⏳ |
| Summary.csv lisible | sans code | ⏳ |
| GNG ≥ 70 | — | ⏳ |

### Gate Sprint 5 — Clôture & Passation
| Critère | Seuil | Status |
|---------|-------|--------|
| ANALYSIS_PROTOCOL.md | adaptation P4 + D1-D4 + écarts | ⏳ |
| Dossier results/ transmis | à instance analyse (JAMAIS agent code) | ⏳ |
| Tiers reproduit scoring | sans code source | ⏳ |
| GNG ≥ 80 | — | ⏳ |

---

## Décision Pivot Finale (BR-010)

> **Règle** : Décision prise APRÈS Sprint 5, SELON SEULS CHIFFRES ci-dessus.

| Condition | Résultat | Action |
|-----------|----------|--------|
| P1 ≥ P2 (Recall ET Precision ET Cost<0.7×) | — | PIVOT → P1 défaut, P2/P3/P4 option traçabilité |
| P3 ≈ P4 (|Δ| < 5pp Recall ET Precision, p≥0.05) | — | Granularité fine = raffinement non prioritaire, P3 référence |
| Sinon (écart significatif Recall ET Precision) | — | Garder P2/P4 tel quel |

---

## Anomalies / Observations

| Date | Pipeline | Cycle | Observation | Action |
|------|----------|-------|-------------|--------|
| — | — | — | — | — |

---

## Notes Méthodologiques

1. **Variance cycles** : IQR sur 5 cycles < 30% médiane (R-STAT-02). Sinon étendre à 10 cycles.
2. **Significativité** : Test McNemar p<0.05 pour Recall/Precision (BR-010).
3. **Coût** : tokens + temps/1000 (approximation relative, même modèle D2).
4. **M06/M07** : Humain requis — flaggé explicite, pas de métrique numérique.

---

*Dernière MAJ : [auto-généré par run_experiment.py]*