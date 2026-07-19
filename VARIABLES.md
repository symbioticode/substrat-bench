# VARIABLES.md — Banc d'essai ETAU/SECS (v0.1)

## BLOC 1 — Identité du projet
```
NOM_CHANTIER    : etau-secs-banc-essai
PROTOCOLE_CIBLE : ETAU_SECS_banc_essai_multisprint_v0_1.md
VERSION_PROTO   : v0.1
SPRINTS_TOTAL   : 5 (Sprint 0 → Sprint 4)
CIBLE_LIVRABLE  : results/ + ANALYSIS_PROTOCOL.md + PROGRESSION.md
```

## BLOC 2 — Équipe & Rôles (§5 protocole)
```
AGENT_CODE      : Claude Code Web (ce document)
INSTANCE_ANALYSE: Opus 4.7 isolé (contexte séparé, post-Sprint 4)
ARBITRE_FINAL   : Andrei (auteur méthodes, décide pivot §0)
LLM_COUNCIL     : 5 sub-agents Sonnet (si décision BR critique)
```

## BLOC 3 — Architecture technique
```
MODELE_UNIQUE_D2: [À DÉCIDER — D2 bloquant Sprint 0]
N_INSTANCES_N   : 3 (par ensemble, §2 protocole)
N_ROUNDS_R      : 2 (P1 débat, §2 protocole)
N_CARTOGRAPHES_M: 2 (P4 passe 2, §2 protocole)
CORPUS_MAX_TOKENS: [À DÉCIDER — D1, doit tenir 1 appel]
SEED_GLOBAL     : 42
N_CYCLES        : 5 (pour absorber variance température, §6 protocole)
TOTAL_LLM_CALLS : ~115 par cycle complet (23 × 5 cycles)
```

## BLOC 4 — Budget tokens & Modèle (D2)
```
MODEL_PROVIDER  : [anthropic|openai|local]
MODEL_NAME      : [ex: claude-3-5-sonnet-20241022, gpt-4o, llama-3.1-70b]
API_KEY_ENV     : [ANTHROPIC_API_KEY | OPENAI_API_KEY]
MAX_TOKENS_CALL : 2000 (par défaut §2bis)
TEMPERATURE     : 0.6 (variance contrôlée, §2 protocole)
BUDGET_ESTIME   : ~115 appels / cycle × 5 cycles = 575 appels
COUT_ESTIME_USD : [À CALCULER selon modèle D2]
```

## BLOC 5 — Corpus & Vérité terrain (D1, §3)
```
CORPUS_SOURCE   : [À CHOISIR — session TI-360 ou brainstorming LocalContext]
ANONYMISATION   : [OUI/NON — noms locuteurs, IDs org]
N_INCIDENTS_MIN : 24 (4 par type × 6 types §3)
TYPES_INCIDENTS :
  - CONTRADICTION_INTRA
  - CONTRADICTION_INTER
  - DERIVE
  - NON_ETAYE
  - LACUNE_SILENCIEUSE
  - AMBIGU_GENUINE
GROUND_TRUTH    : corpus/ground_truth/ground_truth.json (immuable post-génération)
CORPUS_MODIFIE  : corpus/source/corpus_test.json (lu par pipelines)
```

## BLOC 6 — Paramètres d'agrégation & seuils (D4, §2, §4)
```
SIMILARITY_METRIC : cosine (sentence-transformers)
EMBEDDING_MODEL   : sentence-transformers/all-MiniLM-L6-v2 (défaut, rapide)
SIMILARITY_THRESHOLD: [D4 — À VALIDER Sprint 1 sur échantillon manuel]
VOTE_THRESHOLD    : 2/3 (≥2 instances sur 3 pour P1/P2)
CONFIDENCE_LEVELS : P3={FORT, FAIBLE}, P4={FORT, PROBABLE, FAIBLE}
TRACEABILITY_OPT  : P4 Option B (niveau fil, round 2) — D3 par défaut
```

## BLOC 7 — Métriques & Seuils GNG (adapté SKILL-GNG-PAPER EIP)
```
M01_DETECTION_RECALL      : incidents détectés / incidents injectés
M02_LOCALIZATION_PRECISION: détections correctement localisées / détections totales
M03_FALSE_SIGNAL_RATE     : signaux sans incident injecté / signaux totaux
M04_CONFIDENCE_CALIBRATION: exactitude(FORT) vs exactitude(FAIBLE) — P3/P4 only
M05_COST_PER_DETECTION    : (tokens + temps) / vrais positifs
M06_TRACEABILITY_UTILITY  : test aveugle humain (8 assertions, chrono) — MANUEL
M07_CLOSURE_APPROPRIATE   : % non-résolution sur AMBIGU_GENUINE — MANUEL
M08_IMPLEMENTATION_EFFORT : LOC/pipeline + appels LLM/cycle

GNG_THRESHOLDS (par sprint) :
  Sprint 1 (P0,P1)    : ≥ 60 (Solidité expé + Reproductibilité)
  Sprint 2 (P2)       : ≥ 60
  Sprint 3 (P3,P4)    : ≥ 65 (Rigueur théorique isolation + traçabilité)
  Sprint 4 (Métriques) : ≥ 70 (Toutes dimensions)
  Sprint 5 (Clôture)  : ≥ 80 (GO pour passation Analyste)
```

## BLOC 8 — Structure livrables (§8 protocole)
```
banc-essai/
├── README.md
├── requirements.txt
├── CHANGELOG.md
├── PROGRESSION.md
├── STATUS.md
├── VARIABLES.md
├── CLAUDE.md
├── shell.nix
├── init_project.sh
├── corpus/
│   ├── source/
│   │   └── corpus_test.json          # corpus modifié (lu par pipelines)
│   ├── ground_truth/
│   │   └── ground_truth.json         # 24+ incidents, JAMAIS lu par pipelines
│   └── generate_corpus.py            # Sprint 0 — injection incidents
├── pipelines/
│   ├── common/
│   │   ├── isolation.py              # Sprint 1 — isolation réelle + assertions
│   │   ├── agregation.py             # Sprint 1 — clustering + Dawid-Skene
│   │   └── schemas.py                # Schémas sortie P3/P4 (DiAML-inspiré)
│   ├── pipeline_p0.py                # Sprint 1 — passe unique
│   ├── pipeline_p1.py                # Sprint 1 — vote majoritaire isolé
│   ├── pipeline_p2.py                # Sprint 2 — débat multi-rounds
│   ├── pipeline_p3.py                # Sprint 3 — ETAU/SECS allégé
│   └── pipeline_p4.py                # Sprint 3 — ETAU/SECS complet
├── metrics/
│   └── metrics.py                    # Sprint 4 — M01–M08
├── run_experiment.py                 # Orchestrateur : `python run_experiment.py --cycles 5`
└── results/
    └── cycle_<n>/
        ├── raw_outputs/
        ├── metrics_report.json
        ├── summary.csv
        └── ANALYSIS_PROTOCOL.md
```