from scripts.analyze_direct_p0 import TARGETS, detects


def test_detects_exact_signal():
    assertions = [{"source_ref": {"session_id": "s5"}, "dialogue_act": "FlagAmbiguity", "epistemic_state": "N"}]
    assert detects(assertions, TARGETS["genuine_ambiguity"])
    assert not detects(assertions, TARGETS["payment_open_gap"])
