import sys
from types import SimpleNamespace

import pytest

from run_experiment import get_llm_client
from pipelines.common.isolation import _estimated_cost_usd
from pipelines.common.schemas import iter_json_objects, ParseurOutput, parse_dialogue_act, DialogueAct
from pipelines.pipeline_p4 import parse_cartographer_output, parse_nucleus_output
from pipelines.common.prompts import PROMPTS
from metrics.metrics import load_pipeline_results


def test_deepseek_adapter_uses_external_key_and_non_thinking(monkeypatch):
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured["call"] = kwargs
            return SimpleNamespace(choices=[])

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("DEEPSEEK_API_KEY", "secret-not-written")
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    client = get_llm_client("deepseek-v4-flash", "deepseek")
    client.create_message("deepseek-v4-flash", [{"role": "user", "content": "test"}], 20, 0.6)

    assert captured["client"] == {
        "api_key": "secret-not-written", "base_url": "https://api.deepseek.com"
    }
    assert captured["call"]["extra_body"] == {"thinking": {"type": "disabled"}}


def test_deepseek_adapter_requires_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=object))
    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        get_llm_client("deepseek-v4-flash", "deepseek")


def test_deepseek_cost_is_conservative_cache_miss():
    assert _estimated_cost_usd("deepseek", 1_000_000, 1_000_000) == 0.42
    assert _estimated_cost_usd("openai", 1_000_000, 1_000_000) is None


def test_multiline_json_objects_are_parsed_without_line_assumption():
    raw = '{\n  "text": "un",\n  "source_ref": {"session_id": "s", "tour_n": 1}\n}\n' \
          '{"text":"deux","source_ref":{"session_id":"s","tour_n":2}}'
    assert [row["text"] for row in iter_json_objects(raw)] == ["un", "deux"]


def test_json_wrapper_is_flattened_and_capacity_enforced():
    raw = '{"assertions": [' + ','.join(
        f'{{"text":"item-{index}"}}' for index in range(40)
    ) + ']}'
    parsed = list(iter_json_objects(raw, limit=32))
    assert len(parsed) == 32
    assert parsed[-1]["text"] == "item-31"


def test_metrics_loader_accepts_pretty_jsonl_and_applies_capacity(tmp_path):
    path = tmp_path / "raw.jsonl"
    path.write_text("\n".join(
        '{\n  "text": "item-%d",\n  "source_ref": {"session_id": "s", "tour_n": %d}\n}' % (i, i)
        for i in range(40)
    ))
    loaded = load_pipeline_results(path, limit=32)
    assert len(loaded) == 32
    assert loaded[-1]["text"] == "item-31"


def test_parseur_output_skips_invalid_object_and_keeps_following_valid_one():
    raw = '{"text":"incomplet"}\n' \
          '{"text":"valide","dialogue_act":"Inform","epistemic_state":"T",' \
          '"source_ref":{"session_id":"s","tour_n":1}}'
    parsed = ParseurOutput.from_jsonl(raw, "reader")
    assert [assertion.text for assertion in parsed.assertions] == ["valide"]


def test_cartographer_jsonl_zones_become_clusters():
    raw = '{"zone_ref":{"session_id":"s","tour_range":[1,2]},"assertions":[]}\n' \
          '{"zone_ref":{"session_id":"s","tour_range":[3,4]},"assertions":[]}'
    parsed = parse_cartographer_output(raw, "carto_0")
    assert len(parsed["clusters"]) == 2
    assert parsed["cartographe_id"] == "carto_0"


def test_provider_assert_alias_normalizes_to_contract_enum():
    assert parse_dialogue_act("Assert") is DialogueAct.INFORM


def test_nucleus_thread_range_is_anchored_to_first_exact_turn():
    raw = '{"text":"synthèse","dialogue_act":"Assert","epistemic_state":"T",' \
          '"source_ref":{"session_id":"s","tour_range":[3,9]},' \
          '"confidence":"PROBABLE","coherence_level":"MAJORITY"}'
    assertions, zones = parse_nucleus_output(raw)
    assert not zones
    assert len(assertions) == 1
    assert assertions[0].source_ref.tour_n == 3
    assert assertions[0].dialogue_act is DialogueAct.INFORM


def test_extraction_prompts_pre_register_uniform_capacity():
    for key in ("P0_extraction", "P1_round1", "P1_roundN", "P2_extraction",
                "P3_parseur", "P4_parser"):
        assert "32 assertions" in PROMPTS[key]
