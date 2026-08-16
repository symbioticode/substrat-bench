# VARIABLES.md — Banc d'essai ETAU/SECS (v0.3.0)

## BLOC 1 — Identité du projet
```
NOM_CHANTIER    : etau-secs-banc-essai
PROTOCOLE_CIBLE : docs/spec/substrat-bench_PROTOCOL_v0_3_0.md
VERSION_PROTO   : v0.3.0
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
MODELE_UNIQUE_D2: gpt-4.1-mini-2025-04-14
N_INSTANCES_N   : 3 (par ensemble, §2 protocole)
N_ROUNDS_R      : 2 (P1 débat, §2 protocole)
N_CARTOGRAPHES_M: 2 (P4 passe 2, §2 protocole)
CORPUS_MAX_TOKENS: sous la fenêtre D2; mesure exacte consignée avant run
SEED_GLOBAL     : 42
N_CYCLES        : 5 (pour absorber variance température, §6 protocole)
TOTAL_LLM_CALLS : 230 pour A+B; +115 seulement si Cycle C déclenché
```

## BLOC 4 — Budget tokens & Modèle (D2)
```
MODEL_PROVIDER  : openai
MODEL_NAME      : deepseek-v4-flash (mode non-thinking)
API_KEY_ENV     : DEEPSEEK_API_KEY (injectée depuis 61_AGORA/.env, jamais copiée)
MAX_TOKENS_CALL : 4000 (uniforme) + capacité préenregistrée de 32 assertions/réponse
TEMPERATURE     : 0.6 (variance contrôlée, §2 protocole)
BUDGET_ESTIME   : 23 réponses × 5 répétitions × 2 cycles = 230 réponses
COUT_ESTIME_USD : < 1 USD pour A+B, estimation conservatrice avant cache
```

## BLOC 5 — Corpus & Vérité terrain (D1, §3)
```
CORPUS_SOURCE   : LocalContext; segments exacts figés dans prepare_localcontext_source.py
ANONYMISATION   : OUI — identifiants personnels et projet, détails commerciaux et URLs retirés;
                  noms publics de modèles/auteurs conservés lorsque nécessaires au raisonnement
CORPUS_NATURE   : HYBRIDE — 11 tours réels anonymisés + 24 micro-incidents contrôlés,
                  greffés dans deux conversations composites opaques;
                  mesure la détection contrôlée en contexte, pas la fréquence naturelle d'incidents
N_INCIDENTS_MIN : 24 (4 par type × 6 types §3)
TYPES_INCIDENTS :
  - CONTRADICTION_INTRA
  - CONTRADICTION_INTER
  - DERIVE
  - NON_ETAYE
  - LACUNE_SILENCIEUSE
  - AMBIGU_GENUINE
GROUND_TRUTH    : corpus/ground_truth/ground_truth.json (régénération explicite --force seulement;
                  hashes à figer après validation croisée)
CORPUS_MODIFIE  : corpus/source/corpus_test.json (lu par pipelines)
```

## BLOC 6 — Paramètres d'agrégation & seuils (D4, §2, §4)
```
SIMILARITY_METRIC : cosine (sentence-transformers)
EMBEDDING_MODEL   : sentence-transformers/all-MiniLM-L6-v2 (défaut, rapide)
SIMILARITY_THRESHOLD: 0.36 (calibration D4, 50 paires, F1=0.8364)
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
M05_COST_PER_DETECTION    : vecteur {tokens/TP, secondes/TP, coût_USD/TP}; unités jamais additionnées
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
│   ├── pipeline_p1.py                # Sprint 1 — débat multi-rounds
│   ├── pipeline_p2.py                # Sprint 2 — vote majoritaire isolé
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
