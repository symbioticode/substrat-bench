import json
import hashlib
from collections import Counter
from pathlib import Path

from corpus.generate_corpus import (
    SEED, TYPES, build_injections, compose_public_corpus,
    interleave_sessions, normalize_public_metadata,
)

REPO_ROOT = Path(__file__).parents[1]


def test_ground_truth_has_balanced_valid_references():
    corpus = json.loads((REPO_ROOT / "corpus/source/corpus_test.json").read_text())
    truth = json.loads((REPO_ROOT / "corpus/ground_truth/ground_truth.json").read_text())
    refs = {(row["session_id"], row["tour_n"]) for row in corpus}
    incidents = truth["incidents"]
    assert truth["seed"] == SEED
    assert len(incidents) == 24
    assert Counter(row["type"] for row in incidents) == Counter({kind: 4 for kind in TYPES})
    for incident in incidents:
        origin = incident["source_ref_origine"]
        reprise = incident["source_ref_reprise"]
        assert (origin["session_id"], origin["tour_n"]) in refs
        assert (reprise["session_id"], reprise["tour_n"]) in refs


def test_incident_generation_is_deterministic_and_ids_unique():
    first = build_injections()
    second = build_injections()
    assert first == second
    incidents = first[1]
    assert len({row["incident_id"] for row in incidents}) == len(incidents)


def test_public_corpus_does_not_leak_gold_labels_or_synthetic_tail():
    corpus = json.loads((REPO_ROOT / "corpus/source/corpus_test.json").read_text())
    metadata = " ".join(
        f'{row["session_id"]} {row["locuteur"]}' for row in corpus
    ).casefold()
    assert all(kind.casefold() not in metadata for kind in TYPES)
    assert "instance_témoin" not in metadata
    assert all(row["session_id"].startswith("session_") for row in corpus)
    assert {row["locuteur"] for row in corpus} <= {"participant_1", "participant_2"}


def test_public_rows_are_structurally_indistinguishable():
    corpus = json.loads((REPO_ROOT / "corpus/source/corpus_test.json").read_text())
    assert {tuple(row.keys()) for row in corpus} == {
        ("session_id", "tour_n", "locuteur", "texte")
    }
    assert all("provenance" not in row for row in corpus)
    lengths = Counter(row["session_id"] for row in corpus)
    assert set(lengths) == {"session_001", "session_002"}
    assert min(lengths.values()) > 20


def test_interleaving_is_deterministic_and_preserves_session_order():
    source = json.loads((REPO_ROOT / "corpus/source/corpus_source.json").read_text())
    injected, _ = build_injections()
    first = interleave_sessions(source, injected)
    assert first == interleave_sessions(source, injected)
    for session_id in {row["session_id"] for row in first}:
        turns = [row["tour_n"] for row in first if row["session_id"] == session_id]
        assert turns == sorted(turns)

    public_a = normalize_public_metadata(first, build_injections()[1])
    public_b = normalize_public_metadata(first, build_injections()[1])
    assert public_a == public_b


def test_composite_conversations_are_deterministic_and_refs_remapped():
    source = json.loads((REPO_ROOT / "corpus/source/corpus_source.json").read_text())
    injected, incidents = build_injections()
    first = compose_public_corpus(source, injected, incidents)
    assert first == compose_public_corpus(source, injected, incidents)
    corpus, truth = first
    refs = {(row["session_id"], row["tour_n"]) for row in corpus}
    for incident in truth:
        assert (incident["source_ref_origine"]["session_id"],
                incident["source_ref_origine"]["tour_n"]) in refs
        assert (incident["source_ref_reprise"]["session_id"],
                incident["source_ref_reprise"]["tour_n"]) in refs
    for source_session, public_session in (("lc_math", "session_001"),
                                            ("lc_coherence", "session_002")):
        expected = [row["texte"] for row in source if row["session_id"] == source_session]
        positions = [next(i for i, row in enumerate(corpus)
                          if row["session_id"] == public_session and row["texte"] == text)
                     for text in expected]
        assert positions == sorted(positions)


def test_public_corpus_excludes_identified_sensitive_markers():
    content = (REPO_ROOT / "corpus/source/corpus_source.json").read_text().casefold()
    forbidden = ("andrei", "paul", "caroline", "la chamoise", "niort", "http://", "https://")
    assert all(marker not in content for marker in forbidden)


def test_frozen_artifact_hashes_match_manifest():
    manifest = json.loads((REPO_ROOT / "corpus/FREEZE.json").read_text())
    assert manifest["verdict"] == "GEL OUI"
    for relative_path, expected in manifest["files"].items():
        actual = hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()
        assert actual == expected
