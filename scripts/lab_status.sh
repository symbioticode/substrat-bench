#!/usr/bin/env bash
# lab_status.sh - Banc d'essai ETAU/SECS / Tracking (PCA-T)
# Usage: ./scripts/lab_status.sh [--report] [--cycles] [--sync]

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
MODE="${1:-dashboard}"

green()  { printf '\033[0;32m%s\033[0m' "$1"; }
yellow() { printf '\033[0;33m%s\033[0m' "$1"; }
red()    { printf '\033[0;31m%s\033[0m' "$1"; }
blue()   { printf '\033[0;34m%s\033[0m' "$1"; }

# PCA-T1: Detection sprint — STATUS.md > branche git > INDETERMINE (jamais vide silencieux)
detect_sprint() {
  local sprint_label=""

  # 1. Essayer STATUS.md (cherche "Sprint actuel: N" ou "## Sprint courant: N")
  if [[ -f "$REPO_ROOT/STATUS.md" ]]; then
    sprint_label=$(
      grep -Ei "(sprint (actuel|courant)|current sprint)" "$REPO_ROOT/STATUS.md" 2>/dev/null | \
      head -1 | sed -E 's/.*[:#] *//' | sed -E 's/[^0-9].*//' | xargs
    )
  fi

  # 2. Repli sur nom de branche git (retire préfixe sprint- si présent)
  if [[ -z "$sprint_label" ]]; then
    sprint_label=$(git -C "$REPO_ROOT" branch --show-current 2>/dev/null | sed 's/^sprint[-_]//i' | xargs)
  fi

  # 3. Valeur explicite par défaut (jamais vide silencieux)
  if [[ -z "$sprint_label" ]]; then
    echo "INDÉTERMINÉ (STATUS.md et branche git absents/vides)"
  else
    echo "$sprint_label"
  fi
}

# PCA-T2: Checklists declaratives
core_files=(
  "README.md" "CLAUDE.md" "VARIABLES.md" "STATUS.md" "PROGRESSION.md"
  "requirements.txt" "shell.nix" "run_experiment.py" "HYPOTHESES.md" "DECISIONS.md"
)

pipeline_files=(
  "pipelines/pipeline_p0.py"
  "pipelines/pipeline_p1.py"
  "pipelines/pipeline_p2.py"
  "pipelines/pipeline_p3.py"
  "pipelines/pipeline_p4.py"
)

common_files=(
  "pipelines/common/isolation.py"
  "pipelines/common/schemas.py"
  "pipelines/common/agregation.py"
  "pipelines/common/prompts.py"
)

corpus_files=(
  "corpus/generate_corpus.py"
  "corpus/source/corpus_test.json"
  "corpus/ground_truth/ground_truth.json"
)

metrics_files=(
  "metrics/metrics.py"
)

tracking_files=(
  "brainstorm/BR-001.md"
  "brainstorm/BR-002.md"
  "brainstorm/BR-003.md"
  "brainstorm/BR-004.md"
  "brainstorm/BR-005.md"
  "brainstorm/BR-006.md"
  "brainstorm/BR-007.md"
  "brainstorm/BR-008.md"
  "brainstorm/BR-009.md"
  "brainstorm/BR-010.md"
)

# PCA-T3: Trois niveaux de verite (existe / non-vide / substantiel)
check_artifact() {
  local path="$REPO_ROOT/$1"
  if [[ ! -f "$path" ]]; then echo "ABSENT"
  elif [[ ! -s "$path" ]]; then echo "VIDE"
  else
    local lines; lines=$(wc -l < "$path")
    [[ $lines -lt 3 ]] && echo "MINIMAL(${lines}L)" || echo "OK(${lines}L)"
  fi
}

# Vérification substantive pour ground_truth.json (PCA-T3 niveau 3)
check_ground_truth() {
  local path="$REPO_ROOT/corpus/ground_truth/ground_truth.json"
  if [[ ! -f "$path" ]]; then echo "ABSENT"; return; fi
  if [[ ! -s "$path" ]]; then echo "VIDE"; return; fi

  # Parse JSON: structure attendue {"incidents": [...]}
  python3 -c "
import json, sys
try:
    with open('$path') as f:
        data = json.load(f)
    incidents = data.get('incidents', []) if isinstance(data, dict) else data
    from collections import Counter
    c = Counter(i.get('type', 'UNKNOWN') for i in incidents)
    total = len(incidents)
    print(f'TOTAL={total}')
    for t in sorted(c.keys()):
        print(f'{t}={c[t]}')
except Exception as e:
    print(f'ERREUR={e}')
" 2>/dev/null
}

# Vérification cycles A vs B avec provider (PCA-T3 niveau 3)
check_cycles_detail() {
  local results_dir="$REPO_ROOT/results"
  if [[ ! -d "$results_dir" ]]; then
    echo "Aucun dossier results/"
    return
  fi

  local a_dirs b_dirs
  a_dirs=$(find "$results_dir" -maxdepth 1 -name "cycle_A_*" -type d 2>/dev/null | wc -l | tr -d ' ')
  b_dirs=$(find "$results_dir" -maxdepth 1 -name "cycle_B_*" -type d 2>/dev/null | wc -l | tr -d ' ')

  # Provider depuis args run_experiment.py (default mock) ou STATUS.md
  local provider="mock"
  if [[ -f "$REPO_ROOT/STATUS.md" ]]; then
    provider=$(grep -i "provider" "$REPO_ROOT/STATUS.md" | head -1 | sed 's/.*://' | xargs || echo "mock")
  fi

  printf 'Cycle A: %s runs (provider: %s)\n' "$a_dirs" "$provider"
  printf 'Cycle B: %s runs (provider: %s)\n' "$b_dirs" "$provider"
}

# DECISIONS.md : etat D1-D4 (format DEC-XXX avec "EN ATTENTE" ou valeur)
check_decisions() {
  local path="$REPO_ROOT/DECISIONS.md"
  if [[ ! -f "$path" ]]; then
    echo "Fichier absent — à vérifier manuellement"
    return
  fi

  # Cherche DEC-005 (D4), DEC-006 (D3), DEC-007 (D2), DEC-008 (D1)
  local dec
  for n in 005 006 007 008; do
    dec=$(grep -A 10 "^## DEC-${n}" "$path" 2>/dev/null | grep -m1 -i "décision" | sed -E 's/.*[Dd]écision *: *//' | xargs)
    if [[ -n "$dec" ]]; then
      echo "DEC-${n}: ${dec}"
    else
      echo "DEC-${n}: non trouvée"
    fi
  done
}

# PCA-T4: Score par categorie
score_category() {
  local pass=0 total=0
  for f in "$@"; do
    ((total++))
    local st; st=$(check_artifact "$f")
    [[ "$st" == OK* ]] && ((pass++)) || true
  done
  echo "$pass/$total"
}

# PCA-T5: Sante infrastructure Git
git_health() {
  if ! git -C "$REPO_ROOT" rev-parse --git-dir &>/dev/null; then
    printf '    %s\n' "$(red 'Pas de depot Git')"
    return
  fi

  local unpushed last status_porcelain repo_size sensitive
  # Commits non poussés (gère le cas sans upstream)
  if git -C "$REPO_ROOT" rev-parse --abbrev-ref @{u} 2>/dev/null; then
    unpushed=$(git -C "$REPO_ROOT" log @{u}.. --oneline 2>/dev/null | wc -l | tr -d ' ')
  else
    unpushed="N/A (pas de remote configuré)"
  fi

  last=$(git -C "$REPO_ROOT" log -1 --pretty=format:"%h %s (%cr)" 2>/dev/null)
  status_porcelain=$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  repo_size=$(du -sh "$REPO_ROOT/.git" 2>/dev/null | cut -f1)

  # Fichiers sensibles non trackés (alert-only) - || true pour éviter exit sur grep sans match
  sensitive=$(git -C "$REPO_ROOT" status --porcelain 2>/dev/null | grep -E '^\?\?.*(\.env|\.key|api.*key|secret)' -i | head -3 | sed 's/^?? //' | paste -sd '; ' -) || true
  [[ -z "$sensitive" ]] && sensitive="Aucun détecté"

  printf '    Dernier commit   : %s\n' "$last"
  printf '    Non pousses      : %s\n' "$unpushed"
  printf '    Fichiers modif.  : %s\n' "$status_porcelain"
  printf '    Taille .git      : %s\n' "$repo_size"
  printf '    Sensibles (alert): %s\n' "$sensitive"
}

dashboard() {
  printf '\n  Banc d'\''essai ETAU/SECS -- Lab Status  %s\n' "$TIMESTAMP"
  printf '  Sprint : %s\n\n' "$(detect_sprint)"

  local cat name files_str files score
  for cat in "Coeur|${core_files[*]}" \
             "Pipelines|${pipeline_files[*]}" \
             "Commun|${common_files[*]}" \
             "Corpus|${corpus_files[*]}" \
             "Metriques|${metrics_files[*]}" \
             "Tracking|${tracking_files[*]}"; do
    name="${cat%%|*}"
    files_str="${cat#*|}"
    read -ra files <<< "$files_str"
    score=$(score_category "${files[@]}")
    printf '  -- %s (%s) --\n' "$name" "$score"
    for f in "${files[@]}"; do
      local st; st=$(check_artifact "$f")
      case "$st" in
        OK*)     printf '    %s %s\n' "$(green '[OK]')" "$f ($st)" ;;
        ABSENT)  printf '    %s %s\n' "$(red '[--]')" "$f" ;;
        *)       printf '    %s %s\n' "$(yellow '[!!]')" "$f ($st)" ;;
      esac
    done
    echo ""
  done

  # Ground truth detail (substantiel)
  printf '  -- Ground Truth (detail) --\n'
  local gt_detail; gt_detail=$(check_ground_truth)
  if [[ "$gt_detail" == ABSENT ]]; then
    printf '    %s corpus/ground_truth/ground_truth.json\n' "$(red '[--]')"
  elif [[ "$gt_detail" == VIDE ]]; then
    printf '    %s corpus/ground_truth/ground_truth.json (VIDE)\n' "$(yellow '[!!]')"
  elif [[ "$gt_detail" == ERREUR* ]]; then
    printf '    %s Erreur parsing: %s\n' "$(red '[ERR]')" "$gt_detail"
  else
    echo "$gt_detail" | while IFS= read -r line; do
      printf '    %s\n' "$line"
    done
  fi
  echo ""

  # Cycles detail A vs B
  printf '  -- Cycles A/B (detail) --\n'
  check_cycles_detail
  echo ""

  # Decisions D1-D4
  printf '  -- Decisions D1-D4 --\n'
  check_decisions
  echo ""

  # PCA-T5: Sante infrastructure
  printf '  -- Git (PCA-T5) --\n'
  git_health
}

generate_report() {
  mkdir -p "$REPO_ROOT/results"
  local out="$REPO_ROOT/results/status_${TIMESTAMP//:/-}.md"
  {
    echo "# Banc d'essai ETAU/SECS -- Statut $TIMESTAMP"
    echo "**Sprint** : $(detect_sprint)"
    echo ""
    echo "## Artefacts"
    for f in "${core_files[@]}" "${pipeline_files[@]}" "${common_files[@]}" \
             "${corpus_files[@]}" "${metrics_files[@]}" "${tracking_files[@]}"; do
      echo "- \`$f\` : $(check_artifact "$f")"
    done
    echo ""
    echo "## Ground Truth Detail"
    check_ground_truth | sed 's/^/- /'
    echo ""
    echo "## Cycles A/B"
    check_cycles_detail | sed 's/^/- /'
    echo ""
    echo "## Decisions D1-D4"
    check_decisions | sed 's/^/- /'
    echo ""
    echo "## Git Health"
    git_health | sed 's/^/- /'
  } > "$out"
  echo "Rapport : $out"
}

case "$MODE" in
  --report)   generate_report ;;
  --cycles)   find "$REPO_ROOT/results" -maxdepth 1 -name "cycle_*" -type d | sort ;;
  --sync)     git -C "$REPO_ROOT" status --short ;;
  *)          dashboard ;;
esac