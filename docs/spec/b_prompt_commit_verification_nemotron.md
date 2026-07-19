# Prompt de commit et vérification — substrat-bench_PROTOCOL_v0_2_2.md

*À coller après le prompt de cadrage (fichier a). Suppose que le repo `substrat-bench` existe déjà (vide ou avec le squelette précédent) et que git est configuré.*

---

Tâche unique, avant tout autre travail : intégrer le fichier normatif fusionné et prouver qu'aucune dérive n'a eu lieu au passage.

**Avertissement préalable** : `banc-essai/` a déjà un état git non propre (fichiers modifiés et non suivis d'une session antérieure — corpus, pipelines, run_experiment.py, etc.). Ce prompt ne touche à **aucun** de ces fichiers et ne les ajoute pas au commit. Le commit de cette tâche ne contient que `docs/spec/` et `SETUP_LOG.md` — le reste attend une revue humaine séparée, hors de ce prompt.

## Étape 1 — Emplacement

Le script `archive_cleanup_substrat_bench.sh` (exécuté avant ce prompt) a déjà déplacé `substrat-bench_PROTOCOL_v0_2_2.md` vers `banc-essai/docs/spec/`, et archivé les versions dépassées dans `banc-essai/docs/spec/superseded/`. Confirme que c'est bien le cas :

```bash
cd banc-essai
ls docs/spec/substrat-bench_PROTOCOL_v0_2_2.md   # doit exister
ls docs/spec/superseded/                          # doit contenir les versions v0.1, v0.2, v0.2.1, le patch
```

Si le fichier n'est pas à cet emplacement, **arrête-toi** — ne le recrée pas toi-même depuis une autre source, signale l'écart dans `SETUP_LOG.md`.

## Étape 3 — Preuve d'intégrité (bloquant avant commit)

Calcule le hash du fichier tel qu'il est dans ton environnement de travail et compare-le à celui-ci, fourni par l'auteur du document :

```
7fd34486e0759c0ad699269582869698ff41d8cd6a2db7bb6415ad27a1c0c634  substrat-bench_PROTOCOL_v0_2_2.md
```

```bash
sha256sum docs/spec/substrat-bench_PROTOCOL_v0_2_2.md
```

- **Si les deux hashes correspondent exactement** : passe à l'étape 4.
- **Si les deux hashes diffèrent** : **arrête-toi, ne commite rien**. Le fichier a été altéré entre sa création et son arrivée dans ton environnement (encodage, fin de ligne, copie partielle). Signale l'écart dans `SETUP_LOG.md` avec les deux hashes et attends une nouvelle copie du fichier avant de continuer. Ne tente pas de "réparer" le fichier toi-même pour faire correspondre le hash.

## Étape 4 — Vérification structurelle (indépendante du hash, en double contrôle)

Confirme que ces quatre invariants sont bien présents dans le fichier committé — recherche textuelle, pas jugement :

```bash
grep -c "^## " docs/spec/substrat-bench_PROTOCOL_v0_2_2.md          # attendu : 14 titres de section de niveau 2
grep -n "P1.*débat\|P2.*vote majoritaire" docs/spec/substrat-bench_PROTOCOL_v0_2_2.md | head -5
grep -n "1quater" docs/spec/substrat-bench_PROTOCOL_v0_2_2.md        # doit exister : porte de sortie Cycle C
grep -n "Annexe A" docs/spec/substrat-bench_PROTOCOL_v0_2_2.md       # doit exister : personas verbatim
```

Consigne les quatre résultats dans `SETUP_LOG.md`, sous un titre `## Vérification d'intégrité v0.2.2`.

## Étape 5 — Commit

```bash
git add docs/spec/ SETUP_LOG.md
git commit -m "spec: intègre docs/spec/substrat-bench_PROTOCOL_v0_2_2.md (référence normative unique, hash vérifié) + archive versions dépassées"
git tag v0.2.2-reference
```

Un seul commit pour cette étape — pas de commit intermédiaire qui contiendrait une version partielle ou altérée du fichier dans l'historique.

## Étape 6 — Rapport

Dans ta réponse à l'utilisateur, indique uniquement : le résultat de la comparaison de hash (identique / différent), les quatre vérifications de l'étape 4, le tag créé. Pas de résumé narratif du contenu du document — il est déjà lisible par tous dans le repo.

---

*Ce fichier (b) est la seule fois où le contenu de la spec est déplacé vers le repo. Après ce commit, `substrat-bench_PROTOCOL_v0_2_2.md` suit la règle du prompt de cadrage (fichier a) : lecture seule pour tout agent d'exécution.*
