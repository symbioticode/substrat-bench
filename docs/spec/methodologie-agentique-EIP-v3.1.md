# Méthodologie de Déploiement Agentique — Chantier EIP
## Validation Expérimentale du Théorème d'Impossibilité Épistémique

> **Version** : 3.1 · **Statut** : Opérationnel
> **Contexte d'origine** : Adapté de la méthodologie NEUROSYNAPSE-ISR · Mai 2026
> **Mis à jour** : 2026-05-25 — corrections additives : (1) question REV-FINAL "explications alternatives" rétablie (perdue v2→v3) ; (2) Tâche 3 Sprint 0.5 complétée avec question "définition trop forte → trivial ?" (v2) ; (3) scope BR-006 corrigé (tous sprints code, pas seulement 5–6)
> **Destinataires** : Équipe de recherche (1–2 chercheurs) — chantier de validation EIP → papier ICLR 2027

---

## Résumé exécutif

Ce document formalise une approche de production d'un **papier de recherche avec validation expérimentale** en mode **agentique supervisé**. Elle est adaptée directement de la méthodologie NEUROSYNAPSE-ISR (v1.0-BETA) et appliquée à un nouveau contexte : valider empiriquement le Théorème d'Impossibilité Épistémique (TIE / EIP) et ses corollaires, puis produire un article soumettable à ICLR 2027.

**Questions de recherche (v4 — 5 questions)** :
1. *La preuve du TIE est-elle non-circulaire ?* → Lemme d'auditabilité-discrétion (Sprint 7)
2. *Le TIE est-il empiriquement valide ?* → Figure 1 (Sprints 2–3)
3. *Pourquoi les benchmarks MAS textuels plafonnent-ils ?* → Figure 2 (Sprint 5)
4. *Pourquoi RLHF multi-agent est-il fondamentalement borné ?* → Figure 3 (Sprint 5)
5. *Pourquoi les architectures hybrides sont-elles inévitables ?* → Figure 4 (Sprint 6)

> La question 1 est bloquante : sans le Lemme, les questions 2–5 produisent des résultats
> expérimentaux qui ne peuvent pas être rattachés à un théorème rigoureux. Sprint 7 est
> le verrou théorique de tout le chantier.

**Livrable final** : `EIP_paper_vFINAL.md` accompagné de `figures/figure1–4.pdf`, de tables de résultats (`results/`), du code de simulation reproductible (`src/`), de `theory/lemme_auditabilite.md` et d'un `README.md` de reproductibilité.

**Promesse centrale** : ce qui peut être produit par un chercheur seul en 8–11 semaines à raison de 2–3h/jour peut être reproduit par une équipe tierce en moins de 2 semaines en suivant ce guide, sans contact avec l'équipe originale.

**Limite connue** : le quota de tokens Opus est une ressource rare. La qualité est encodée dans la structure — pas dans le budget de tokens.

---

## Partie 1 — Pourquoi cette approche ?

### 1.1 Le problème que cette méthodologie résout

Produire un papier de recherche avec validation expérimentale mobilise quatre types de travail en parallèle :

1. **Travail théorique** — formaliser les définitions, vérifier la cohérence logique, produire des preuves sans circularité
2. **Travail expérimental** — implémenter les canaux, calibrer les paramètres, exécuter les simulations de façon reproductible
3. **Travail rédactionnel** — écrire les sections du papier en respectant les contraintes de format ICLR (pages, style, figures)
4. **Travail de contrôle qualité** — vérifier la cohérence interne (preuves ↔ expériences ↔ claims), identifier les angles morts, évaluer la soumettabilité

Ces quatre travaux ont des profils cognitifs différents. Les confier à une seule instance sans structure produit invariablement des angles morts. La méthodologie compartimente ces travaux de façon explicite.

### 1.2 Ce qui rend cette approche différente d'une utilisation standard de l'IA

| Utilisation standard | Cette approche |
|---------------------|----------------|
| Prompt unique → texte → correction manuelle | Pipeline de sprints avec critères de passage formalisés |
| L'IA valide positivement ses propres productions | Analyste isolé (Opus + extended thinking) sans accès aux conversations de travail |
| La qualité dépend de la mémoire de la conversation | La source de vérité est le repo GitHub — la conversation est éphémère, le repo est permanent |
| Le score de qualité est subjectif | SKILL-GNG-PAPER produit un score Go/No-Go numérique avant chaque sprint |
| Les décisions architecturales sont implicites | Toute décision est tracée dans `brainstorm/BR-XXX.md` avec statut PROPOSÉ / ADOPTÉ / REJETÉ / REMPLACÉ |
| Les failles de preuve sont découvertes tard | Analyse adversariale multi-LLM dès Sprint 0 — les trous sont identifiés avant de coder |

---

## Partie 2 — Les cinq piliers

### Pilier 1 — La source de vérité est le repo, pas la conversation

Toute production se termine par un commit. Toute session commence par `git pull`. Les conversations Claude Code / Jules sont éphémères par construction.

**Implication pratique** : `STATUS.md` est à jour en fin de chaque session. Un collaborateur qui clonerait le repo saurait exactement où en est le chantier : quelles expériences sont complètes, quelles figures sont validées, quelles sections du papier sont en révision.

### Pilier 2 — Les sprints sont atomiques

Un sprint = un objectif = un livrable = un critère de validation. Le Sprint 0.5 produit uniquement les définitions formelles. Le Sprint 7 produit uniquement le lemme de non-circularité. Pas de sprint à double objectif.

**Pourquoi ça compte** : un chantier de recherche dérive parce que les objectifs sont flous. Un sprint atomique ne peut pas dériver — soit le livrable est produit et validé, soit le sprint est relancé avec un correctif documenté.

### Pilier 3 — L'Analyste est isolé

Chaque sprint clé produit un `reviews/REV-Sx.md` généré par une instance Opus distincte (extended thinking activé) qui n'a accès qu'aux fichiers commités. L'Analyste ne sait pas comment le livrable a été produit — il évalue ce qui lui est soumis.

**Ce que ça évite** : l'effet miroir où l'IA évalue positivement ce qu'elle-même a produit. Pour un papier scientifique, cet effet est particulièrement dangereux car il masque les circularités dans les preuves et les faiblesses dans les protocoles expérimentaux.

### Pilier 4 — Les règles opérationnelles sont numérotées

Toute règle de gestion porte un identifiant `R-XXXXX`. Elle est invocable par référence dans n'importe quelle conversation. `"Appliquer R-PREUVE-01"` déclenche le bon comportement sans ambiguïté.

**Avantage** : les règles survivent à la rotation de contexte de l'IA et à la fatigue du chercheur en fin de session.

### Pilier 5 — Le score GNG-PAPER est calculé dès Sprint 2

Le score Go/No-Go (SKILL-GNG-PAPER) est calculé à partir du Sprint 2 pour chaque livrable. Un score < 60 bloque la progression. Il évalue spécifiquement : rigueur des preuves, solidité expérimentale, reproductibilité, clarté rédactionnelle, honnêteté sur les limitations.

---

## Partie 3 — Architecture du déploiement

### 3.1 Le cycle opérationnel

```
CHERCHEUR
  │
  ├─ Session : Prépare Sprint N (lit STATUS.md, prépare les inputs)
  │            Détermine l'instance IA optimale (voir matrice §3.2)
  │
  ▼
INSTANCE IA (Claude Code Web / Jules) ◄──────────────────────────────┐
  │                                                                   │
  ├─ Lecture CLAUDE.md + STATUS.md + dernier REV-S(N-1)              │
  ├─ Exécution sprint (matrice modèles, personas adversariaux)        │
  ├─ Production livrable + commit                                     │
  ├─ Génération REV-Sx.md (instance Analyste isolée — Opus)          │
  └─ Mise à jour STATUS.md + commit final                            │
                                                                      │
CHERCHEUR                                                             │
  ├─ Lecture REV-Sx.md                                                │
  ├─ Vérification score GNG-PAPER                                     │
  ├─ Approbation OR retour correctif via issue GitHub                 │
  └─ Si approbation : déclenche sprint suivant ──────────────────────►┘
```

### 3.2 La matrice des modèles

| Tâche | Modèle recommandé | Justification |
|-------|-------------------|---------------|
| Formalisation théorique, preuves, gap analysis littérature | **Opus 4.7 + extended thinking** | Raisonnement multi-étapes, littérature scientifique |
| **Sprint 7 — Lemme de non-circularité** | **Opus 4.7 + extended thinking** | Preuve formelle — raisonnement déductif profond requis |
| L'Analyste (`REV-Sx.md`) | **Opus 4.7 + extended thinking + instance isolée** | Regard externe simulé, slow reasoning forcé |
| Décisions architecturales BR (voir R-COUNCIL-01) | **LLM Council (5 sub-agents Claude)** | Angles méta-cognitifs absents des personas de domaine |
| Implémentation code Python, rédaction sections papier | **Jules (Google) ou Sonnet** | Qualité d'exécution, économise tokens Opus |
| Corrections post-REV, reformulations | **Sonnet** | Tâche d'exécution, pas d'invention conceptuelle |
| Comptage (pages ICLR, chars), GNG-PAPER, calculs statistiques | **Haiku** | Tâches structurées répétables, coût minimal |

> **Note sur Jules** : pour les sprints à dominante code (Sprints 1, 2, 3), Jules est préféré à Claude Code Web car il dispose d'un environnement bash persistant et peut exécuter les scripts Python directement. Le basculement vers Claude Code Web se fait pour les sprints à dominante théorique (Sprints 0.5, 7) et rédactionnelle (Sprint 4).

**Règle d'or** : Opus est une ressource rare. Ne l'utiliser que quand le raisonnement profond est irremplaçable — preuves formelles, évaluation critique, décisions d'architecture. Sprint 7 est un usage justifié.

### 3.3 Les personas adversariaux (adaptés au contexte EIP)

Quatre sub-agents sont configurés avec des postures épistémiques distinctes pour attaquer chaque livrable avant qu'il soit soumis à l'Analyste :

**Persona A — La Théoricienne de l'Information Sceptique**
- Profil : reviewer ISIT / IEEE Transactions on Information Theory, 20 ans de théorie de Shannon
- Posture : les théorèmes d'impossibilité en information doivent être démontrés formellement, pas illustrés empiriquement
- Questions types :
  - « La définition d'auditabilité est-elle indépendante de la définition de canal discret, ou y a-t-il une circularité ? »
  - « Le Lemme d'auditabilité-discrétion est-il démontré, ou seulement affirmé ? »
  - « L'effondrement du gradient est-il une conséquence triviale de la discrétisation, ou un résultat non évident ? »
  - « Quelle est la généralité du résultat au-delà de GPT-2 small ? »

**Persona B — L'Expérimentateur Reproductibilité**
- Profil : ML engineer spécialisé reproductibilité (NeurIPS Reproducibility Challenge)
- Posture : un résultat non reproductible est un non-résultat
- Questions types :
  - « Est-ce que deux chercheurs indépendants obtiendraient exactement la même Figure 1 en suivant le README ? »
  - « Les seeds sont-ils fixés partout ? Les dépendances versionnées exactement ? »
  - « La calibration de γ_i est-elle déterministe ou stochastique ? Si stochastique, l'IQR est-il rapporté ? »

**Persona C — Le Rédacteur ICLR**
- Profil : Area Chair ICLR, exige clarté, positionnement, et honnêteté sur les limitations
- Posture : un bon papier ICLR a un claim clair, une expérience propre, et ne survend pas
- Questions types :
  - « Quel est le claim en une phrase ? Peut-on le vérifier directement avec la Figure 1 ? »
  - « Le Lemme est-il présenté comme un résultat nouveau, ou comme une conséquence triviale ? »
  - « Les limitations sont-elles honnêtement déclarées dans la section 7, ou minimisées ? »
  - « Le positionnement par rapport à RecursiveMAS est-il équitable ? »

**Persona D — Le Critique des Preuves**
- Profil : logicien / philosophe des sciences, spécialiste des théorèmes d'impossibilité (Arrow, Gödel, CAP)
- Posture : les théorèmes d'impossibilité ont des hypothèses cachées — il faut les expliciter
- Questions types :
  - « La définition d'auditabilité dans le Lemme est-elle primitive ou dérivée ? »
  - « Les trois conditions (a), (b), (c) de la définition d'auditabilité sont-elles toutes nécessaires ? »
  - « Sous quelles conditions le théorème ne s'applique-t-il pas ? »
  - « L'Étape 3 de la preuve (canal continu → espace connexe → image constante dans O_cert dénombrable) est-elle correcte avec la topologie de O_cert héritée ? »

**Porte de sortie documentée** : si 3/4 personas convergent avec l'instance de travail (= biais de substrat actif), recourir aux IA externes (DeepSeek-R1, Gemini 2.0 Pro, Mistral Large) pour un regard vraiment externe. Cette décision est tracée dans `brainstorm/BR-001.md` — elle n'est posée qu'une fois.

> **Note v3 :** l'analyse adversariale conduite sur ALL-AnswersEIP.md (5 LLMs : Grok,
> Perplexity, Gemini, Mistral, DeepSeek) a précisément joué ce rôle de porte de sortie
> pour Sprint 7. Le résultat — convergence sur le même trou dans la preuve — a déclenché
> la création de Sprint 7. Ce cas est documenté dans BR-010.

---

## Partie 4 — Sprints détaillés

### Sprint 0 — Préparation infrastructure (Manuel, 2h)

**Objectif** : poser les fondations du chantier v4 — 5 questions de recherche, 7 sprints, 4 figures + 1 lemme.

**Actions** :
```
□ Créer repo GitHub : epistemic-impossibility-validation
□ Exécuter init_project.sh → arborescence standard (voir Annexe A v4)
□ Compléter VARIABLES.md (voir §4.1 — 8 blocs dont BLOC 8 mis à jour v4)
□ Compléter CLAUDE.md (instructions pour Claude Code Web)
□ Initialiser STATUS.md (Sprint courant = 0, statut = PRÊT, version = v4)
□ Vérifier connectivity Claude Code Web / Jules ↔ GitHub
□ Vérifier que GPT-2 small est téléchargeable (HuggingFace Hub)
□ Vérifier que PyTorch 2.x est installé ou disponible en env
□ Commiter l'arborescence vide + README.md squelette

  — Infrastructure corollaires —
□ Créer src/experiment_corollaries.py (squelette vide)
□ Créer src/experiment_hybrid.py (squelette vide)
□ Créer results/learning_curves.csv (en-têtes seuls)
□ Créer results/rlhf_propagation.csv (en-têtes seuls)
□ Créer results/hybrid_comparison.csv (en-têtes seuls)
□ Créer results/source_correlation.csv (en-têtes seuls)

  — Infrastructure Sprint 7 (nouveau v4) —
□ Créer theory/lemme_auditabilite.md (squelette vide)
□ Créer theory/theorem71_formal.md (squelette vide — sera rempli Sprint 0.5 puis révisé Sprint 7)

  — Décisions architecturales — LLM Council (R-COUNCIL-01) —
□ Lancer LLM Council sur BR-002 (k-NN vs Deep EK-NN pour γ_i) → council-report-BR002.html commité
□ Lancer LLM Council sur BR-004 (Dempster O1 vs Rule O3 de Denœux) → council-report-BR004.html commité
□ BR-001 à BR-010 créés avec statut PROPOSÉ (BR-010 = analyse adversariale multi-LLM)
□ Quota tokens Opus 4.7 connu et budget estimé (voir BLOC 4 : ~8 sessions Opus)
□ Décision : utilise-t-on Jules pour les sprints code ? (documenter dans BR-006)
□ R-PI-01 : régime de propriété intellectuelle des co-auteurs documenté (si applicable)
```

**Livrable** : repo initialisé, `STATUS.md` à jour, arborescence v4 complète.

**Critère de passage** : `git clone` + `pip install -r requirements.txt` fonctionne sans erreur sur une machine tierce. Les 10 fichiers BR existent avec statut PROPOSÉ.

---

### Sprint 0.5 — Formalisation théorique préalable (Opus, 2.5 jours)

**Objectif** : formaliser les définitions — en particulier la définition d'auditabilité en trois conditions (a), (b), (c) — qui seront utilisées dans le Lemme (Sprint 7). Sprint 0.5 pose les définitions ; Sprint 7 démontre le Lemme à partir de ces définitions.

> ⚠️ Coordination avec Sprint 7 : Sprint 0.5 Tâche 1 doit produire une définition
> d'auditabilité avec les trois conditions (a), (b), (c) explicitement séparées.
> Si cette séparation n'est pas faite en Sprint 0.5, Sprint 7 devra la refaire —
> duplication de travail évitable.

**Actions** :

*Tâche 1 — Définitions formelles (1 jour)*

Rédiger `theory/theorem71_formal.md` (version provisoire — sera complétée en Sprint 7) avec :
- **Canal discret** : espace de sortie O au plus dénombrable et finiment descriptible
- **Auditabilité (3 conditions séparées)** :
  - (a) Il existe une machine de Turing M qui s'arrête sur toute sortie o ∈ O
  - (b) M produit "valide" si et seulement si o satisfait un prédicat décidable Φ
  - (c) Chaque sortie certifiée a une représentation finie et unique
- **Gradient-preserving** : ∃ c > 0 tel que ‖J_C(h)‖₂ ≥ c pour tout h dans l'espace latent
- **Certifiable** : message appartenant à un schéma JSON validé, ou formule logique, ou fonction de masse sur un cadre fini

*Tâche 2 — Isomorphisme Belnap flou / TBM (0.5 jour)*

Rédiger `theory/belnap_tbm_isomorphism.md` : preuve formelle de l'isomorphisme entre l'espace de Belnap flou (Perry & Tsoukias 1998) et les fonctions de masse sur {T, F, B, N} (Smets 1994).

*Tâche 3 — Vérification non-circularité préliminaire (0.5 jour)*

Soumettre à l'Analyste (Opus isolé) les deux questions suivantes :

- « La définition d'auditabilité en trois conditions (a), (b), (c) suppose-t-elle déjà la discrétion, ou la dérive-t-elle ? »
- « La définition est-elle trop forte au point de rendre le théorème trivial — c'est-à-dire : existe-t-il une définition strictement plus faible qui suffirait encore à dériver le Lemme ? » *(rétabli de v2)*

> Note : si l'Analyste répond que la circularité est présente dès Sprint 0.5, corriger
> avant de passer à Sprint 1. Sprint 7 ne peut pas fermer un trou que Sprint 0.5 n'a
> pas ouvert correctement.

*Tâche 4 — Cadrage théorique des corollaires (0.5 jour)*

Rédiger `theory/corollary_framework.md` établissant la chaîne déductive TIE → Corollaires 1, 2, 3.

*Tâche 5 — LLM Council sur le framing de recherche (30 min)*

Invoquer le LLM Council sur : « Le chantier v4 répond-il aux 5 bonnes questions de recherche pour ICLR 2027, dans le bon ordre, avec la bonne portée ? »

**Livrable** :
- `theory/theorem71_formal.md` (version provisoire avec définitions)
- `theory/belnap_tbm_isomorphism.md`
- `theory/corollary_framework.md`
- `paper/EIP_paper_v0.1.md` (squelette avec structure v4)
- `brainstorm/council-report-framing-S05.html`

**Critère de passage** :
- REV-S0.5 confirme que les trois conditions d'auditabilité sont séparées et non-circulaires.
- L'Analyste attribue score GNG-PAPER ≥ 65 sur la section théorique.
- Le LLM Council ne soulève pas d'objection bloquante sur le framing.

---

### Sprint 1 — Instrumentation des canaux (Jules + Opus pour calibration, 1.5 jour)

*(Inchangé depuis v3 — voir BR-2026-CHANTIER-VALIDATION-v4.md)*

---

### Sprint 2 — Expérience principale (Jules, 2.5 jours)

*(Inchangé depuis v3 — voir BR-2026-CHANTIER-VALIDATION-v4.md)*

---

### Sprint 3 — Analyse, figures, tables (Haiku + Sonnet, 1.5 jour)

*(Inchangé depuis v3 — voir BR-2026-CHANTIER-VALIDATION-v4.md)*

---

### Sprint 7 — Lemme de non-circularité ⚠️ [NOUVEAU v4]
**(Opus + extended thinking — Travail purement théorique, 2 jours)**
**Séquence : après Sprint 3, avant Sprint 4**

> **Pourquoi avant Sprint 4 :** Sprint 4 rédige le papier final. La section 3
> (Théorème 7.1) ne peut pas être rédigée définitivement sans le Lemme.
> Sprint 7 est le verrou théorique de la rédaction.

> **Pourquoi après Sprint 3 :** Sprint 7 est purement théorique — il ne dépend
> pas des résultats expérimentaux. Il peut s'exécuter en parallèle des Sprints
> 1–3 si les ressources le permettent. Le point de synchronisation obligatoire
> est avant Sprint 4.

**Contexte :** l'analyse adversariale conduite sur cinq LLMs indépendants
(ALL-AnswersEIP.md) a identifié que le Théorème 7.1 suppose implicitement
"auditable ⇒ discret" sans le démontrer. DeepSeek (section 3.3) formule le
diagnostic le plus précis. Gemini identifie le théorème du point fixe de
Lawvere comme mécanisme générateur sous-jacent. Mistral propose l'argument
de cardinalité de Cantor comme stratégie de preuve la plus directe.

### Tâche 7.1 — Démonstration du Lemme (1 jour)

**Énoncé :**

> **Lemme (Auditabilité → Discrétion)**
> Soit C un canal de communication dont l'espace de sortie est O.
> Si C est auditable au sens des trois conditions (a), (b), (c) définies
> en Sprint 0.5, alors l'ensemble O_cert des sorties certifiées est
> au plus dénombrable.

**Stratégies de preuve — dans l'ordre de solidité :**

**Stratégie A — Argument de calculabilité (préférée)**
```
1. Par condition (a), M est une machine de Turing qui s'arrête sur tout o ∈ O_cert.
2. L'ensemble des entrées sur lesquelles une machine de Turing s'arrête est
   récursivement énumérable (thèse de Church-Turing).
3. Tout ensemble récursivement énumérable est dénombrable (par définition :
   il existe une surjection de ℕ vers l'ensemble).
4. Donc O_cert est dénombrable. ∎

Vérification non-circularité : cette preuve ne suppose pas que O est discret.
Elle dérive la dénombrabilité de la décidabilité de M. La condition (c)
(représentation finie et unique) n'est pas utilisée ici — elle sert dans
Stratégie B et comme condition de robustesse.
```

**Stratégie B — Argument de cardinalité (Cantor)**
```
1. Par condition (c), chaque sortie certifiée a une représentation finie
   et unique sur un alphabet fini (le schéma de validation).
2. L'ensemble des chaînes finies sur un alphabet fini est dénombrable
   (Cantor : bijection avec ℕ via encodage de Gödel ou indexation lexicographique).
3. La condition (c) induit une injection de O_cert dans cet ensemble.
4. Tout sous-ensemble d'un ensemble dénombrable est dénombrable.
5. Donc O_cert est dénombrable. ∎

Note : Stratégie B dépend de la condition (c). Si (c) est affaiblie
(représentation non-unique, ou alphabet infini), la preuve tombe.
Vérifier que la condition (c) est nécessaire pour l'auditabilité
réelle dans les systèmes CLAIM (schéma JSON fini, alphabet fini). ✓
```

**Stratégie C — Argument topologique (Sard, complément)**
```
Si C est C¹ et gradient-preserving (jacobien de rang plein p.p.)
et si O_cert est l'image entière de C sur ℳ connexe :
- Par le théorème de Sard, l'ensemble des valeurs critiques a mesure nulle.
- Un ensemble dénombrable dans un espace de dimension > 0 a mesure nulle.
- Une application continue d'un espace connexe vers un espace discret
  est constante — contradiction avec le gradient non-nul.

Stratégie C est un argument de cohérence géométrique, pas un remplacement
de Stratégie A ou B. Elle renforce la preuve mais ne la constitue pas seule.
```

**Critère de sélection :** produire les deux démonstrations A et B.
Stratégie C comme appendice. L'Analyste décidera laquelle intégrer
en preuve principale dans le papier (Tâche 7.2).

### Tâche 7.2 — Vérification de non-circularité résiduelle par l'Analyste (0.5 jour)

Soumettre `theory/lemme_auditabilite.md` à l'Analyste (Opus isolé, extended thinking)
avec les trois questions suivantes :

**Test 1 — Circularité :**
La définition d'auditabilité utilisée dans les Stratégies A et B suppose-t-elle
déjà la discrétion, ou la dérive-t-elle ? Identifier toute hypothèse cachée.

**Test 2 — Nécessité des conditions :**
Les trois conditions (a), (b), (c) sont-elles toutes nécessaires pour que
le Lemme tienne ? Si l'une d'elles peut être supprimée sans que la preuve
s'effondre, la définition est trop forte.

**Test 3 — Suffisance pour le Théorème 7.1 :**
La dénombrabilité de O_cert suffit-elle pour que l'Étape 3 du Théorème 7.1
(canal continu → espace connexe → image constante dans O_cert dénombrable)
soit correcte ? En particulier : si O_cert hérite d'une topologie non-discrète
de O, le raisonnement de connectivité tient-il encore ?

**Critère de passage Tâche 7.2 :**
- Test 1 : OUI (pas de circularité détectée)
- Test 2 : OUI (les trois conditions sont nécessaires) OU identification précise
  de la condition superflue avec proposition d'allégement
- Test 3 : OUI avec justification sur la topologie de O_cert

Si NON à l'un des tests : retour à Tâche 7.1 avec le diagnostic précis de l'Analyste.
Tracer le retour dans BR-010 avec statut RETOUR-S7.1.

### Tâche 7.3 — Intégration dans Théorème 7.1 (0.5 jour)

Réécrire `theory/theorem71_formal.md` (version finale) pour incorporer
le Lemme comme Étape 0 explicite :

```
Théorème 7.1 (Impossibilité Épistémique) — Version non-circulaire

Hypothèses :
  H1 : C est un canal de communication avec espace latent d'entrée
       (ℳ, g) — variété riemannienne lisse, connexe, dim(ℳ) > 0.
  H2 : C est gradient-preserving : ∃ c > 0, ∀ h ∈ ℳ, ‖J_C(h)‖₂ ≥ c.
  H3 : C est auditable au sens des conditions (a), (b), (c).

Étape 0 — Lemme (voir theory/lemme_auditabilite.md) :
  Par H3, O_cert est dénombrable.

Étape 1 :
  Par H1, ℳ est connexe et non-dénombrable (dim > 0).

Étape 2 :
  Toute application continue C : ℳ → O_cert d'un espace connexe
  vers un espace dénombrable (muni de la topologie discrète) est
  constante. [Justification topologie O_cert : voir REV-S7.]

Étape 3 :
  Une application constante a un jacobien identiquement nul,
  ce qui contredit H2.

Conclusion : H1, H2, H3 sont mutuellement incompatibles. ∎
```

**Livrable Sprint 7 :**
```
theory/lemme_auditabilite.md        ← NOUVEAU (Stratégies A + B + C)
theory/theorem71_formal.md          ← MIS À JOUR (Étape 0 intégrée)
reviews/REV-S7.md                   ← Rapport Analyste (Tests 1, 2, 3)
```

**Critère de passage Sprint 7 :**
- REV-S7 : Test 1 OUI (pas de circularité)
- REV-S7 : Test 2 OUI ou allégement documenté
- REV-S7 : Test 3 OUI avec justification topologique
- Score GNG-PAPER ≥ 70 sur la section théorique

**Instance :** Opus 4.7 + extended thinking (Tâches 7.1, 7.3) +
Opus isolé (Tâche 7.2 — Analyste).

---

### Sprint 4 — Rédaction et révision du papier (Opus Analyste + Sonnet, 2 jours)
**Conditionné à Sprint 7 ✓**

**Objectif** : intégrer tous les résultats dans `EIP_paper_vFINAL.md`.

**Sections à compléter ou réviser :**
- Section 3.1 : définitions formelles depuis `theory/theorem71_formal.md` (version Sprint 7)
- Section 3.2 : Lemme d'auditabilité-discrétion — présenter comme résultat intermédiaire
- Section 3.3 : Théorème 7.1 — preuve complète avec Étape 0 intégrée
- Section 4 : insérer Figure 1, Table 1, Table 2, Table 3
- Section 5.5 : harmoniser terminologie Belnap flou
- Section 6.3 : résultats condition D (conflit injecté)
- Section 7 — Limitations : calibration γ_i, généralité au-delà de GPT-2 small,
  portée du Lemme (condition (c) et finitude de l'alphabet)

**REV-FINAL par l'Analyste (Opus isolé)** — questions soumises :
1. Le Lemme est-il présenté de façon à ce que sa nouveauté soit claire sans survente ?
2. Les résultats empiriques supportent-ils le Théorème sans survente ?
3. Y a-t-il des explications alternatives aux résultats que les auteurs n'ont pas considérées ? *(rétabli de v2)*
4. Le protocole est-il reproductible par une équipe tierce en suivant le README ?
5. Le papier est-il soumettable à ICLR 2027 dans cet état ?
6. La définition d'auditabilité est-elle suffisamment rigoureuse pour une
   communauté de théoriciens de l'information ?
7. Le positionnement par rapport à RecursiveMAS est-il équitable ?

**Livrable** : `EIP_paper_vFINAL.md` + `reviews/REV-FINAL.md` + `README.md`

**Critère de passage** : score GNG-PAPER ≥ 80. README testé sur machine tierce.

---

### Sprint 5 — Corollaires benchmarks et RLHF (Sonnet, 2 jours)

*(Inchangé depuis v3 — voir BR-2026-CHANTIER-VALIDATION-v4.md)*

---

### Sprint 6 — Corollaire inévitabilité hybride (Opus, 1.5 jours)

*(Inchangé depuis v3 — voir BR-2026-CHANTIER-VALIDATION-v4.md)*

---

## Partie 5 — SKILL-GNG-PAPER

*(Inchangé depuis v2)*

### Grille d'évaluation (100 points)

| Dimension | Points | Critères |
|-----------|--------|----------|
| **Rigueur théorique** | 25 | Définitions non circulaires, preuves complètes, hypothèses explicites, **Lemme démontré** |
| **Solidité expérimentale** | 25 | Protocole reproductible, N suffisant, tests statistiques appropriés, barres d'erreur |
| **Reproductibilité** | 20 | README opérationnel, seeds fixés, dépendances versionnées, résultats bit-à-bit pour canal C |
| **Clarté rédactionnelle** | 15 | Claim clair en une phrase, figures lisibles, positionnement honnête |
| **Honnêteté sur les limitations** | 15 | Section 7 complète, plan de contingence documenté, généralité déclarée |

### Seuils

| Score | Statut | Action |
|-------|--------|--------|
| ≥ 80 | **GO** | Soumission possible |
| 65–79 | **GO conditionnel** | Corrections mineures avant soumission |
| 60–64 | **NO-GO** | Corrections majeures — nouveau REV requis |
| < 60 | **NO-GO bloquant** | Retour au sprint précédent |

### Application par sprint

| Sprint | Seuil minimum | Dimensions évaluées |
|--------|--------------|---------------------|
| Sprint 0.5 | ≥ 65 | Rigueur théorique uniquement |
| Sprint 2 | ≥ 60 | Solidité expérimentale + Reproductibilité |
| Sprint 3 | ≥ 65 | Toutes les dimensions sauf Clarté rédactionnelle |
| **Sprint 7** | **≥ 70** | **Rigueur théorique uniquement — Lemme** |
| Sprint 4 | ≥ 80 | Toutes les dimensions |

---

## Partie 6 — Traçabilité des décisions architecturales

*(Format BR inchangé depuis v2)*

### 6.3 Décisions pré-tracées (à remplir en Sprint 0)

| ID | Décision | Statut initial | Council requis |
|----|----------|----------------|----------------|
| BR-001 | Stratégie anti-biais de substrat (personas vs IA externes) | PROPOSÉ | Non |
| BR-002 | Calibration γ_i : k-NN vs Deep EK-NN | PROPOSÉ | **Oui — Sprint 0** |
| BR-003 | Modèle de base : GPT-2 small (117M) | PROPOSÉ | Non |
| BR-004 | Règle de combinaison TBM : Dempster normalisé (O1) vs Rule O3 (Denœux) | PROPOSÉ | **Oui — Sprint 0** |
| BR-005 | Valeur initiale θ_conflit : 0.3 (prior avant calibration empirique) | PROPOSÉ | Non |
| BR-006 | Disponibilité Jules pour tous les sprints code (1, 2, 3, 5, 6) — ou fallback GitHub Actions | PROPOSÉ | Non |
| BR-007 | Tâche collaborative synthétique Sprints 5–6 : classification 4 classes | PROPOSÉ | Non |
| BR-008 | Framing recherche v4 : 5 questions dans le bon ordre pour ICLR 2027 | PROPOSÉ | **Oui — Sprint 0.5** |
| BR-009 | Critère de stricte supériorité hybride (Figure 4 : gap minimum acceptable) | PROPOSÉ | Non |
| BR-010 | Stratégie de preuve du Lemme : Stratégie A (calculabilité) vs B (Cantor) | PROPOSÉ | Non |

> **BR-010 — nouveau v4 :** la décision entre Stratégie A et Stratégie B pour le Lemme
> est tracée ici. L'Analyste (REV-S7) tranche. La décision est adoptée après REV-S7
> et intégrée dans `theory/theorem71_formal.md` par Tâche 7.3.

---

## Partie 7 — Règles opérationnelles

### Règles héritées (inchangées)

| ID | Règle |
|----|-------|
| R-DOC-01 | Maximum 4 fichiers documentation core dans le repo. |
| R-DEC-01 | Toute décision d'architecture est tracée dans `brainstorm/BR-XXX.md`. |
| R-QO-01 | Toute question non résolue est tracée avec identifiant QO-Sn-XX. |
| R-GNG-01 | Score GNG-PAPER calculé après chaque sprint à partir de Sprint 0.5. Un score < 60 bloque. |
| R-REV-01 | REV-Sx.md produit par une instance Analyste isolée (Opus + extended thinking). |
| R-CALC-01 | Tout calcul numérique vérifié par Haiku indépendamment. |
| R-PREUVE-01 | Aucune preuve n'est complète tant que l'Analyste n'a pas confirmé l'absence de circularité. |
| R-PREUVE-02 | Toute preuve formelle référence explicitement ses hypothèses. |
| R-REPRO-01 | Toute expérience est reproductible : seed fixé, dépendances versionnées. |
| R-REPRO-02 | Le canal C (CLAIM) doit être bit-à-bit identique entre deux runs avec le même seed. |
| R-STAT-01 | Toute comparaison inclut un test statistique et des barres d'erreur (IQR sur 50 runs). |
| R-STAT-02 | N = 50 runs minimum. Si IQR > 30% de la médiane, augmenter à N = 100. |
| R-TRL-PAPER-01 | Le papier n'affiche pas un claim plus fort que ce que démontrent les expériences. |
| R-BR-01 | Tout changement de décision adoptée déclenche une mise à jour du REV en cours. |
| R-ICLR-01 | Le papier respecte les contraintes ICLR 2027 : 9 pages max, double colonne, anonymisé. |
| R-CONFLIT-01 | La condition D (conflit injecté) est exécutée systématiquement sur le canal CLAIM. |
| R-COUNCIL-01 | Le LLM Council est invoqué si et seulement si : décision architecturale BR + deux options défendables + erreur coûteuse après le sprint suivant. |
| R-COROL-01 | Chaque corollaire référence explicitement ses hypothèses supplémentaires au-delà du TIE. |
| R-HYBRIDE-01 | L'Expérience 6A doit montrer une supériorité stricte de l'architecture hybride sur les deux axes (p < 0.05). |

### Règles nouvelles (Sprint 7 — v3)

| ID | Règle |
|----|-------|
| R-LEMME-01 | Le Lemme d'auditabilité-discrétion doit être démontré indépendamment du Théorème 7.1. Aucune étape de la preuve du Lemme ne peut référencer le Théorème, ni vice-versa pour les étapes qui précèdent l'Étape 0. |
| R-LEMME-02 | La définition d'auditabilité utilisée dans le Lemme est celle établie en Sprint 0.5 avec les trois conditions (a), (b), (c) explicitement séparées. Toute modification de cette définition après Sprint 0.5 est tracée dans BR-010 et déclenche automatiquement une re-validation par l'Analyste. |
| R-LEMME-03 | Le Lemme est présenté dans le papier comme un résultat intermédiaire nécessaire, pas comme une contribution principale. Sa nouveauté est dans sa fonction — fermer le trou dans la preuve — pas dans sa difficulté mathématique intrinsèque. |
| R-SEQ-01 | Sprint 4 (rédaction) ne peut pas démarrer si REV-S7 n'a pas rendu un verdict GO sur les trois tests (non-circularité, nécessité, suffisance). Cette règle est non-négociable. |

---

## Partie 8 — Checklist de démarrage Sprint 0 (v4)

```
  — Fondations repo —
□ VARIABLES.md complété et commité (8 blocs — voir §4.1)
□ Repo GitHub créé avec branch principale (main)
□ CLAUDE.md au format Claude Code Web
□ STATUS.md initialisé (Sprint courant = 0, statut = PRÊT, VERSION = v4)
□ Arborescence v4 créée via init_project.sh (inclut theory/lemme_auditabilite.md)
□ README.md squelette commité
□ requirements.txt créé : Python 3.11+, PyTorch 2.x, transformers, matplotlib, seaborn, scipy, pandas

  — Vérifications techniques —
□ GPT-2 small téléchargeable (test : from transformers import GPT2Model sans erreur)
□ PyTorch 2.x installé et CPU-only fonctionnel (test : torch.manual_seed(42))
□ Connectivity Claude Code Web / Jules ↔ GitHub testée (lecture + commit)

  — Décisions architecturales —
□ BR-001 à BR-010 créés avec statut PROPOSÉ
□ LLM Council lancé sur BR-002 (γ_i) → council-report-BR002.html commité
□ LLM Council lancé sur BR-004 (règle de combinaison O1 vs O3) → council-report-BR004.html commité
□ Quota tokens Opus 4.7 connu et budget estimé pour ~8 sessions Opus (v4)
□ Décision Jules disponibilité pour tous les sprints code (1, 2, 3, 5, 6) documentée dans BR-006
□ R-PI-01 : régime de propriété intellectuelle des co-auteurs documenté (si applicable)
```

### §4.1 VARIABLES.md pour ce chantier (v4)

```
BLOC 1 — Identité du projet
  NOM_CHANTIER    : epistemic-impossibility-validation
  THEOREME_CIBLE  : Théorème d'Impossibilité Épistémique (EIP / TIE)
  TARGET_CONF     : ICLR 2027
  DEADLINE_SOUM   : Octobre 2026
  VERSION_CHANTIER: v4 (5 questions, 7 sprints)

BLOC 2 — Équipe
  PI              : Andrei
  CO_AUTEURS      : [à compléter]
  CONTACT_PI      : [email]

BLOC 3 — Architecture technique
  MODELE_BASE       : GPT-2 small (117M paramètres, HuggingFace)
  N_CANAUX          : 3 (A=texte, B=latent, C=CLAIM)
  N_AGENTS          : 3 (émetteur, récepteur, orchestrateur)
  N_RUNS            : 50 par condition (extensible à 100 si variance élevée)
  SEED_GLOBAL       : 42
  NIVEAUX_ENTROPIE  : {0.05, 0.1, 0.2, 0.5, 1.0, 2.0}
  NIVEAUX_CONFLIT   : {0.0, 0.2, 0.5, 0.8}
  N_ROUNDS_COROL    : 200 (Exp 5A courbes d'apprentissage)
  N_ROUNDS_RLHF     : 100 (Exp 5B propagation RLHF)
  NIVEAUX_CONFIANCE : {0.3, 0.6, 0.9}
  ARCHITECTURES     : {texte_seul, latent_seul, CLAIM_seul, hybride}
  N_CLASSES_TACHE   : 4 (Θ = {ami, ennemi, neutre, inconnu})

BLOC 4 — Budget tokens (v4 révisé)
  SESSIONS_OPUS   : ~8 (Sprint 0.5 ×2 tâches, Sprint 7 ×2 tâches,
                        REV-S2, REV-S3, Sprint 6 design, REV-FINAL)
  SESSIONS_SONNET : ~8 (Sprints 1 rédaction, 4, 5 exécution, corrections)
  SESSIONS_JULES  : ~6 (Sprints 1 code, 2, 3, 5, 6)
  SESSIONS_HAIKU  : ~5 (vérifications GNG, stats, comptage ICLR)

BLOC 5 — Repo GitHub
  GITHUB_USER     : [à compléter]
  GITHUB_REPO     : epistemic-impossibility-validation
  BRANCH_PRINCIPALE: main

BLOC 6 — Modèles IA
  MODEL_THEORIQUE  : claude-opus-4-7 (extended thinking)
  MODEL_ANALYSTE   : claude-opus-4-7 (instance isolée, extended thinking)
  MODEL_COUNCIL    : claude-sonnet-4-6 (5 sub-agents LLM Council)
  MODEL_REDACTION  : claude-sonnet-4-x
  MODEL_CODE       : Jules (Google) ou claude-sonnet-4-x
  MODEL_VERIFICATION: claude-haiku-3-x

BLOC 7 — Domaine de recherche
  PROBLEME_EIP     : Impossibilité d'un canal simultanément
                     gradient-preserving et auditable
  LEMME_CIBLE      : Auditabilité → Discrétion (dénombrabilité de O_cert)
  STRATEGIE_PREUVE : A (calculabilité) ou B (Cantor) — décidé par REV-S7
  HYPOTHESE_NULL_1 : Les trois canaux ont le même profil de gradient
  HYPOTHESE_ALT_1  : Canal texte s'effondre quand entropie → 0   (Figure 1)
  HYPOTHESE_NULL_2 : Canal texte et latent ont la même courbe d'apprentissage
  HYPOTHESE_ALT_2  : Canal texte plafonne avant round 100         (Figure 2)
  HYPOTHESE_NULL_3 : Signal RLHF identique quelle que soit la confiance
  HYPOTHESE_ALT_3  : Signal RLHF → 0 pour agent confiant κ > 0.7 (Figure 3)
  HYPOTHESE_NULL_4 : Latent seul suffit pour les deux propriétés
  HYPOTHESE_ALT_4  : Seule l'architecture hybride satisfait les deux axes (Figure 4)
  CONCURRENTS     : RecursiveMAS (Yang et al. 2026), DIAL (Lazaridou 2020)
  CRITERES_ICLR   : Clarté du claim, solidité expérimentale, reproductibilité

BLOC 8 — Structure papier v4
  SECTION_1 : Introduction — La dichotomie manquante
  SECTION_2 : Background — Latent MAS, protocoles, belief functions
  SECTION_3 : TIE — Théorème non-circulaire
              3.1 Définitions (auditabilité 3 conditions, gradient-preserving)
              3.2 Lemme d'auditabilité-discrétion       ← Sprint 7
              3.3 Théorème 7.1 — preuve complète        ← Sprint 7
              3.4 Généralisation IB + Figure 1          ← Sprint 2-3
  SECTION_4 : Epistemic Interface Problem — Définition formelle
  SECTION_5 : CLAIM comme solution — 5 invariants + orchestrateur
  SECTION_6 : Validation expérimentale
              6.1 Figure 1 — Gradient vs entropie (TIE)
              6.2 Figure 2 — Plafonnement benchmarks
              6.3 Figure 3 — Borne RLHF multi-agent
              6.4 Figure 4 — Inévitabilité hybride
              6.5 Table corrélation cachée (Rule O3)
  SECTION_7 : Calibration problem + Limitations (dont portée du Lemme)
  SECTION_8 : Discussion et travaux futurs
```

---

## Partie 9 — Ce que cette approche ne règle pas

**Limite 1 — Le biais de substrat n'est pas éliminé**
Les personas adversariaux l'atténuent. Sur un sujet à l'intersection théorie de l'information / ML / logique non-classique, un panel d'experts humains reste supérieur à des personas IA pour détecter les hypothèses cachées. L'analyse multi-LLM (ALL-AnswersEIP.md) a montré sa valeur en identifiant le trou dans la preuve — mais elle ne remplace pas la relecture par un théoricien de l'information humain avant soumission.

**Limite 2 — La calibration γ_i reste ouverte**
Si k-NN et Deep EK-NN échouent tous les deux (correlation < 0.5), le plan de contingence (masse uniforme) réduit la force du claim sur le canal C.

**Limite 3 — La généralité au-delà de GPT-2 small n'est pas testée**
La validité du Théorème 7.1 sur d'autres architectures est un travail futur.

**Limite 4 — Le Lemme suppose la finitude de l'alphabet de certification**
La Stratégie B repose sur la condition (c) — représentation finie et unique des sorties certifiées. Si un système d'auditabilité utilise un alphabet infini (ex. représentation en précision arbitraire), la Stratégie B tombe. La Stratégie A (calculabilité) reste valide dans ce cas — mais la portée du Lemme doit être déclarée honnêtement en Section 7.

**Limite 5 — La méthodologie ne remplace pas le jugement stratégique**
Elle produit un papier de haute qualité. Elle ne remplace pas le jugement humain sur le choix du journal, du workshop, des co-auteurs, et du moment de soumission.

**Limite 6 — Jules est un outil externe non garanti**
Si Jules n'est pas disponible, le Sprint 2 doit se faire localement. Résoudre au Sprint 0.

---

## Annexe A — Arborescence du repo (v4)

```
epistemic-impossibility-validation/
├── README.md
├── CHANGELOG.md
├── QUICK_START.md
├── REPO_STRUCTURE.md
├── STATUS.md
├── VARIABLES.md                 # 8 blocs (v4)
├── CLAUDE.md
├── requirements.txt
├── init_project.sh
│
├── theory/
│   ├── theorem71_formal.md          # Sprint 0.5 (provisoire) → Sprint 7 (final)
│   ├── belnap_tbm_isomorphism.md    # Sprint 0.5
│   ├── corollary_framework.md       # Sprint 0.5
│   └── lemme_auditabilite.md        # Sprint 7 ← NOUVEAU v4
│
├── src/
│   ├── channels.py                  # Sprint 1
│   ├── calibration.py               # Sprint 1
│   ├── experiment.py                # Sprint 2
│   ├── analysis.py                  # Sprint 3
│   ├── experiment_corollaries.py    # Sprint 5
│   └── experiment_hybrid.py         # Sprint 6
│
├── results/
│   ├── raw_results.csv              # Sprint 2
│   ├── conflict_results.csv         # Sprint 2
│   ├── learning_curves.csv          # Sprint 5A
│   ├── rlhf_propagation.csv         # Sprint 5B
│   ├── hybrid_comparison.csv        # Sprint 6A
│   └── source_correlation.csv       # Sprint 6B
│
├── figures/
│   ├── figure1.pdf                  # Sprint 3
│   ├── figure2_learning_curves.pdf  # Sprint 5
│   ├── figure3_rlhf_bound.pdf       # Sprint 5
│   ├── figure4_architecture.pdf     # Sprint 6
│   ├── table1.tex
│   ├── table2_latency.tex
│   └── table3_theta.tex
│
├── paper/
│   ├── EIP_paper_v0.1.md        # Sprint 0.5 (structure v4, 8 sections)
│   ├── EIP_paper_v0.3.md        # Post-Sprint 3
│   ├── EIP_paper_v0.5.md        # Post-Sprint 5
│   └── EIP_paper_vFINAL.md      # Sprint 4 (après Sprint 7) → révisé post-Sprint 6
│
├── brainstorm/
│   ├── BR-001.md  ← BR-009.md   # (inchangés)
│   ├── BR-010.md                # Stratégie de preuve du Lemme ← NOUVEAU v4
│   ├── council-report-BR002.html
│   ├── council-report-BR004.html
│   └── council-report-framing-S05.html
│
└── reviews/
    ├── REV-S0.5.md
    ├── REV-S2.md
    ├── REV-S3.md
    ├── REV-S7.md              # ← NOUVEAU v4
    ├── REV-S5.md
    ├── REV-S6.md
    └── REV-FINAL.md
```

---

## Annexe B — Leçons apprises (à compléter post-déploiement)

| ID | Hypothèse à tester | Résultat | Date |
|----|-------------------|----------|------|
| LA-EIP-01 | Les personas adversariaux détectent des angles morts que l'instance de travail ne détecterait pas | À renseigner post-Sprint 0.5 | — |
| LA-EIP-02 | k-NN est suffisant pour calibrer γ_i (correlation > 0.7) | À renseigner post-Sprint 1 | — |
| LA-EIP-03 | N=50 runs donne une variance acceptable (IQR < 30% de la médiane) | À renseigner post-Sprint 2 | — |
| LA-EIP-04 | Jules peut exécuter experiment.py sans intervention manuelle | À renseigner Sprint 2 | — |
| LA-EIP-05 | L'Analyste (Opus isolé) détecte une faiblesse que l'instance de travail n'a pas vue | À renseigner post-REV-S2 | — |
| LA-EIP-06 | Le score GNG-PAPER < 65 au Sprint 0.5 est un signal assez tôt pour corriger sans reprendre la théorie | À renseigner post-REV-S0.5 | — |
| LA-EIP-07 | Un chercheur tiers peut reproduire la Figure 1 en suivant README.md sans contact avec l'équipe | À renseigner post-Sprint 4 | — |
| LA-EIP-08 | Le LLM Council (Tâche 5 Sprint 0.5) soulève une objection sur le framing v4 que les 4 personas ne voient pas | À renseigner post-Sprint 0.5 | — |
| LA-EIP-09 | N=200 rounds est suffisant pour observer le plafonnement du canal texte (Exp 5A) | À renseigner post-Sprint 5 | — |
| LA-EIP-10 | Rule O3 de Denœux détecte > 90% des cas de corrélation cachée (Exp 6B) | À renseigner post-Sprint 6 | — |
| LA-EIP-11 | L'architecture hybride est strictement supérieure (p < 0.05) à chacun des 3 canaux purs sur les deux axes (Exp 6A) | À renseigner post-Sprint 6 | — |
| LA-EIP-12 | Les corollaires v4 suivent formellement du TIE sans hypothèses supplémentaires cachées | À renseigner post-REV-S0.5 | — |
| LA-EIP-13 | La Stratégie A (calculabilité) est retenue par l'Analyste comme preuve principale du Lemme | À renseigner post-REV-S7 | — |
| LA-EIP-14 | L'Analyste confirme que les trois conditions (a),(b),(c) sont toutes nécessaires (aucune superflue) | À renseigner post-REV-S7 | — |
| LA-EIP-15 | L'analyse adversariale multi-LLM (5 modèles) détecte des failles que les 4 personas internes ne voient pas | **OUI** — ALL-AnswersEIP.md a identifié le trou dans la preuve du Théorème 7.1 | 2026-05-24 |

---

## Différences clés avec les versions précédentes

| Dimension | v2.0 | v3.0 (ce document) |
|-----------|------|---------------------|
| **Questions de recherche** | 4 (Figures 1–4) | **5 (+ Lemme)** |
| **Sprints** | 6 | **7 (+ Sprint 7)** |
| **Séquence** | 0→0.5→1→2→3→4→5→6 | **0→0.5→1→2→3→[7]→4→5→6** |
| **Verrou théorique** | Sprint 0.5 seul | **Sprint 0.5 + Sprint 7** |
| **Règles nouvelles** | R-COUNCIL-01, R-COROL-01, R-HYBRIDE-01 | **+ R-LEMME-01/02/03, R-SEQ-01** |
| **BR pré-tracées** | BR-001 à BR-009 | **BR-001 à BR-010** |
| **Budget Opus** | ~6 sessions | **~8 sessions** |
| **Durée estimée** | 7–10 semaines | **8–11 semaines** |
| **Limite documentée** | 5 limites | **6 limites (+ portée du Lemme)** |
| **Leçon apprise confirmée** | 0 | **1 (LA-EIP-15 : analyse multi-LLM validée)** |

**Rationalité de Sprint 7 :** sans le Lemme, le Théorème 7.1 est une tautologie élégante.
Avec le Lemme, c'est une contrainte formelle sur l'architecture des systèmes multi-agents.
La différence entre les deux n'est pas cosmétique — elle détermine si le papier survit
à la relecture d'un théoricien de l'information hostile. 2 jours Opus pour fermer ce trou
est le meilleur investissement du chantier.

---

*Document vivant — Version 3.1 — Mis à jour 2026-05-25 (corrections additives : REV-FINAL Q3 rétablie, Tâche 3 Sprint 0.5 complétée, BR-006 scope corrigé)*
*Usage interne — Projet EIP · Mai 2026*
