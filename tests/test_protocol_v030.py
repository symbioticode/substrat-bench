import json
import hashlib
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(REPO_ROOT))

from pipelines.common.schemas import DialogueAct, EpistemicState, SourceRef, StructuredAssertion, ParseurOutput
from pipelines.common.personas import get_persona_for_instance, PERSONA_FILES, PERSONA_POSTURES, PERSONA_DIR
from pipelines.pipeline_p0 import run_p0
from pipelines.pipeline_p3 import run_p3_arbitre
from metrics.metrics import compute_metrics, match_assertion_to_incident
from pipelines.pipeline_p1 import run_p1_debate
from pipelines.pipeline_p2 import aggregate_p2_vote
from pipelines.common.agnos_observability import AgnosEventWriter
import run_experiment


class RecordingClient:
    def __init__(self):
        self.messages = []
        self.kwargs = []

    def create_message(self, model, messages, max_tokens, temperature, **kwargs):
        self.messages.append(messages[0]["content"])
        self.kwargs.append(kwargs)
        marker = f"sortie-{len(self.messages)}"
        text = json.dumps({
            "text": marker,
            "dialogue_act": "Inform",
            "epistemic_state": "T",
            "source_ref": {"session_id": "s1", "tour_n": 1},
        })
        content = [type("Content", (), {"text": text})()]
        return type("Response", (), {"content": content})()


def assertion(instance, text="incident"):
    return StructuredAssertion(
        text=text,
        dialogue_act=DialogueAct.INFORM,
        source_ref=SourceRef("s1", 1),
        epistemic_state=EpistemicState.T,
        parseur_id=instance,
    )


def test_p1_round_two_contains_every_other_round_one_output():
    client = RecordingClient()
    traces = run_p1_debate(client, "mock", "corpus", provider="mock")
    assert len(traces) == 3
    assert all(len(trace.rounds) == 2 for trace in traces)
    assert [call["seed"] for call in client.kwargs] == [42000, 42001, 42002, 42003, 42004, 42005]
    round_two_prompts = client.messages[3:]
    for index, prompt in enumerate(round_two_prompts):
        expected = {f"sortie-{i}" for i in (1, 2, 3)} - {f"sortie-{index + 1}"}
        assert all(marker in prompt for marker in expected)


def test_strict_majority_rejects_ties_and_accepts_majorities():
    four_tie = [[assertion(f"i{i}")] if i < 2 else [] for i in range(4)]
    six_tie = [[assertion(f"i{i}")] if i < 3 else [] for i in range(6)]
    assert aggregate_p2_vote(four_tie, required_votes=3) == []
    assert aggregate_p2_vote(six_tie, required_votes=4) == []
    four_majority = [[assertion(f"i{i}")] if i < 3 else [] for i in range(4)]
    six_majority = [[assertion(f"i{i}")] if i < 4 else [] for i in range(6)]
    assert len(aggregate_p2_vote(four_majority, required_votes=3)) == 1
    assert len(aggregate_p2_vote(six_majority, required_votes=4)) == 1


def test_persona_order_repeats_vtc():
    assert [get_persona_for_instance(f"p2_instance_{i}") for i in range(6)] == [
        "verificateur_coherence", "traceur_provenance", "cartographe_fils_ouverts",
        "verificateur_coherence", "traceur_provenance", "cartographe_fils_ouverts",
    ]


def test_normative_personas_are_loaded_verbatim():
    expected_hashes = {
        "persona_verificateur.md": "7eb62c8b9e9f8918a31cce6088bc61289b14c59f218d3c07ddb3a1d7d68f8632",
        "persona_traceur.md": "dbe019928a1333e4b1d08344532d66e98cc9f74b7687b85ee79b0c24de8b1a7e",
        "persona_cartographe.md": "4ed2713621f8319bc14a2d8750a8fcdfa711139bc433f081c15b2853e97916df",
    }
    for name, filename in PERSONA_FILES.items():
        content = (PERSONA_DIR / filename).read_text(encoding="utf-8")
        assert hashlib.sha256(content.encode()).hexdigest() == expected_hashes[filename]
        assert PERSONA_POSTURES[name] == content.strip()


def test_arbiter_context_hides_source_reader_and_persona_mapping():
    outputs = [ParseurOutput(f"p3_parseur_{i}", [assertion(f"p3_parseur_{i}")]) for i in range(3)]
    client = RecordingClient()
    run_p3_arbitre(client, "mock", outputs, provider="mock", reader_order=[2, 0, 1])
    prompt = client.messages[0]
    assert "p3_parseur_" not in prompt
    assert "PERSONA ASSIGNÉE" not in prompt
    assert all(f'reader_{i}' in prompt for i in range(3))


def test_p0_is_identical_across_cycles_and_corpus_is_injected_once(tmp_path):
    prompts = []
    for label in ("A", "B"):
        client = RecordingClient()
        run_p0(client, "mock", "CORPUS_UNIQUE", tmp_path / label,
               cycle_label=label, provider="mock")
        prompts.append(client.messages[0])
    assert prompts[0] == prompts[1]
    assert prompts[0].count("CORPUS_UNIQUE") == 1


def test_matching_requires_d4_text_similarity_and_m05_keeps_units_separate():
    incident = {"incident_id": "I1", "type": "DERIVE",
                "description_courte": "projection mars sans confirmation",
                "source_ref_origine": {"session_id": "s1", "tour_n": 1},
                "source_ref_reprise": {"session_id": "s1", "tour_n": 2}}
    unrelated = {"text": "température du serveur", "epistemic_state": "N",
                 "source_ref": {"session_id": "s1", "tour_n": 1}}
    related = {"text": "projection mars sans confirmation", "epistemic_state": "N",
               "source_ref": {"session_id": "s1", "tour_n": 1}}
    assert match_assertion_to_incident(unrelated, [incident]) is None
    assert match_assertion_to_incident(related, [incident]) == incident
    metrics = compute_metrics([related], [incident], {
        "llm_responses": 2, "input_tokens": 100, "output_tokens": 20,
        "wall_time_ms": 50, "estimated_cost_usd": None,
    })
    assert metrics["M05_cost_per_detection"] == {
        "llm_responses_per_tp": 2.0, "input_tokens_per_tp": 100.0,
        "output_tokens_per_tp": 20.0, "wall_time_ms_per_tp": 50.0,
        "estimated_cost_usd_per_tp": None,
    }


def test_mock_full_repetition_writes_exactly_23_ledger_rows(tmp_path):
    repo = Path(__file__).parents[1]
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([{"session_id": "s1", "tour_n": 1, "locuteur": "A", "texte": "fait"}]))
    output = tmp_path / "results"
    completed = subprocess.run(
        [sys.executable, str(repo / "run_experiment.py"), "--cycles", "1", "--personas", "off",
         "--provider", "mock", "--corpus", str(corpus), "--output", str(output), "--skip-metrics",
         "--run-id", "test-run-001"],
        cwd=repo, capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    rows = [json.loads(line) for line in (output / "inference_ledger.jsonl").read_text().splitlines()]
    assert len(rows) == 23
    assert {key: sum(row["pipeline"] == key for row in rows) for key in ("P0", "P1", "P2", "P3", "P4")} == {
        "P0": 1, "P1": 6, "P2": 6, "P3": 4, "P4": 6,
    }
    assert all(row["input_tokens"] is None and row["estimated_cost_usd"] is None for row in rows)
    manifest = json.loads(next((output / "cycle_A_0" / "raw_outputs").glob("*prefix_manifest.json")).read_text())
    assert manifest["prefixes"]["P2@3"] == manifest["prefixes"]["P2@6"][:3]
    assert manifest["prefixes"]["P2@4"] == manifest["prefixes"]["P2@6"][:4]

    events = [json.loads(line) for line in (output / "agnos_events.jsonl").read_text().splitlines()]
    assert len(events) == 12  # runner début/fin + cinq pipelines début/fin
    required_v2 = {
        "agent_id", "timestamp", "statut", "tâche", "détail",
        "cycle_vie", "sante", "resultat",
    }
    assert all(required_v2 <= event.keys() for event in events)
    assert all(event["run_id"] == "test-run-001" for event in events)
    assert events[0]["agent_id"] == "substrat-runner"
    assert events[0]["cycle_vie"] == "actif"
    assert events[-1]["agent_id"] == "substrat-runner"
    assert events[-1]["statut"] == "succès"
    assert events[-1]["cycle_vie"] == "termine"
    assert {event["agent_id"] for event in events[1:-1]} == {
        "substrat-p0", "substrat-p1", "substrat-p2", "substrat-p3", "substrat-p4",
    }
    assert all(event["resultat"] == "indetermine" for event in events)


def test_agnos_reports_pipeline_exception_as_technical_error(tmp_path):
    def failing_pipeline(**kwargs):
        raise RuntimeError("provider indisponible")

    original = run_experiment.PIPELINE_FUNCS.get("PX")
    run_experiment.PIPELINE_FUNCS["PX"] = failing_pipeline
    try:
        event_path = tmp_path / "agnos.jsonl"
        results = run_experiment.run_cycle(
            cycle_num=2,
            pipelines=["PX"],
            client=RecordingClient(),
            model="mock",
            corpus_text="corpus",
            output_base=tmp_path,
            cycle_label="B",
            agnos_writer=AgnosEventWriter(event_path, "error-run"),
        )
    finally:
        if original is None:
            del run_experiment.PIPELINE_FUNCS["PX"]
        else:
            run_experiment.PIPELINE_FUNCS["PX"] = original

    events = [json.loads(line) for line in event_path.read_text().splitlines()]
    assert "error" in results[0]
    assert [event["statut"] for event in events] == ["en_cours", "échec"]
    assert events[-1]["cycle_vie"] == "termine"
    assert events[-1]["sante"] == "erreur"
    assert events[-1]["resultat"] == "indetermine"
    assert events[-1]["cycle"] == "B"
    assert events[-1]["repetition"] == 2
