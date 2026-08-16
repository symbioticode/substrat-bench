#!/usr/bin/env python3
"""Prépare le corpus réel LocalContext choisi par D1=B."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SEGMENTS = {
    "lc_math": [(103, 103, "humain"), (107, 179, "instance_eip"),
                (181, 181, "humain"), (185, 191, "instance_eip")],
    "lc_coherence": [(3, 18, "humain"), (24, 71, "instance_coherence"),
                     (74, 100, "humain"), (104, 161, "instance_coherence"),
                     (165, 179, "humain"), (181, 219, "instance_coherence"),
                     (221, 225, "humain")],
}
REPLACEMENTS = {
    "La Chamoise": "entreprise pilote", "LocalContext": "projet étudié",
    "LC-MATH": "cadre mathématique", "LC-Math": "cadre mathématique", "Copilote": "instance critique",
    "Copilot": "instance critique", "sessions_excerpt.md": "synthèse antérieure",
    "Prompt MULTI-IA – Analyse de modélisation.txt": "analyse multi-instance",
    "Copilote_Review.txt": "revue de l’instance critique",
}


def extract(lines: list[str], start: int, end: int) -> str:
    text = "\n".join(lines[start - 1:end]).strip()
    # Les formes longues doivent être remplacées avant leurs sous-chaînes.
    for source, replacement in sorted(REPLACEMENTS.items(), key=lambda item: -len(item[0])):
        text = text.replace(source, replacement)
    return re.sub(r"https?://\S+", "[URL RETIRÉE]", text)


def prepare(session_1: Path, session_5: Path) -> list[dict]:
    sources = {"lc_math": session_1.read_text(encoding="utf-8").splitlines(),
               "lc_coherence": session_5.read_text(encoding="utf-8").splitlines()}
    corpus = []
    for session_id, segments in SEGMENTS.items():
        for turn_n, (start, end, speaker) in enumerate(segments, start=1):
            corpus.append({"session_id": session_id, "tour_n": turn_n,
                           "locuteur": speaker,
                           "texte": extract(sources[session_id], start, end),
                           "provenance": {"source": "corpus privé anonymisé",
                                          "lignes_origine": f"{start}-{end}"}})
    return corpus


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-1", type=Path, required=True)
    parser.add_argument("--session-5", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("corpus/source/corpus_source.json"))
    args = parser.parse_args()
    corpus = prepare(args.session_1, args.session_5)
    if any(not row["texte"] for row in corpus):
        raise ValueError("segment vide après extraction")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] {len(corpus)} tours anonymisés → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
