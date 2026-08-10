from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.direct_p0_pilot import conservative_cost, in_window


def test_window():
    tz = ZoneInfo("America/Toronto")
    assert in_window(datetime(2026, 8, 10, 0, 0, tzinfo=tz))
    assert not in_window(datetime(2026, 8, 10, 4, 0, tzinfo=tz))


def test_cache_creation_cost():
    assert conservative_cost("anthropic", {
        "cache_creation_input_tokens": 1_000_000, "output_tokens": 0,
    }) == 3.75
