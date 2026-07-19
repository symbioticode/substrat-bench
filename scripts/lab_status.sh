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

# PCA-T1: Detection sprint depuis STATUS.md
detect_sprint() {
  if [[ -f "$REPO_ROOT/STATUS.md" ]]; then
    grep -E "## Sprint courant" "$REPO_ROOT/STATUS.md" 2>/dev/null | head -1 | sed 's/.*: *//'
  else
    echo "inconnu"
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

# PCA-T3: Trois niveaux de verite
check_artifact() {
  local path="$REPO_ROOT/$1"
  if [[ ! -f "$path" ]]; then echo "ABSENT"
  elif [[ ! -s "$path" ]]; then echo "VIDE"
  else
    local lines; lines=$(wc -l < "$path")
    [[ $lines -lt 3 ]] && echo "MINIMAL(${lines}L)" || echo "OK(${lines}L)"
  fi
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

  # PCA-T5: Sante infrastructure
  local n_cycles n_results
  n_cycles=$(find "$REPO_ROOT/results" -maxdepth 1 -name "cycle_*" -type d 2>/dev/null | wc -l | tr -d ' ')
  n_results=$(find "$REPO_ROOT/results" -name "*.csv" -o -name "metrics_report.json" 2>/dev/null | wc -l | tr -d ' ')
  printf '  -- Resultats --\n'
  printf '    Cycles executes : %s\n' "$n_cycles"
  printf '    Fichiers metriques : %s\n\n' "$n_results"

  printf '  -- Git --\n'
  if git -C "$REPO_ROOT" rev-parse --git-dir &>/dev/null; then
    local unpushed last
    unpushed=$(git -C "$REPO_ROOT" log @{u}.. --oneline 2>/dev/null | wc -l | tr -d ' ')
    last=$(git -C "$REPO_ROOT" log -1 --pretty=format:"%h %s (%cr)" 2>/dev/null)
    printf '    Dernier commit : %s\n' "$last"
    printf '    Non pousses    : %s\n' "$unpushed"
    if [[ -f "$REPO_ROOT/.env" ]]; then
      msg=$(yellow 'PRESENT (ne jamais commiter)')
      printf '    .env           : %s\n' "$msg"
    fi
  else
    err_msg=$(red 'Pas de depot Git')
    printf '    %s\n' "$err_msg"
  fi
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
    echo "## Cycles"
    echo "- Cycles executes : $(find "$REPO_ROOT/results" -maxdepth 1 -name "cycle_*" -type d 2>/dev/null | wc -l | tr -d ' ')"
    echo "- Metriques : $(find "$REPO_ROOT/results" -name "*.csv" -o -name "metrics_report.json" 2>/dev/null | wc -l | tr -d ' ')"
  } > "$out"
  echo "Rapport : $out"
}

case "$MODE" in
  --report)   generate_report ;;
  --cycles)   find "$REPO_ROOT/results" -maxdepth 1 -name "cycle_*" -type d | sort ;;
  --sync)     git -C "$REPO_ROOT" status --short ;;
  *)          dashboard ;;
esac