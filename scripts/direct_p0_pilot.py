#!/usr/bin/env python3
"""Pilote P0 direct Anthropic↔DeepSeek, fenêtré, caché et budgété."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, time as wall_time, timezone
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODELS = (
    "anthropic:claude-sonnet-4-5-20250929",
    "deepseek:deepseek-v4-flash",
)
RATES = {
    "anthropic": {"input": 3.0, "output": 15.0},
    # Plafond volontairement supérieur au tarif public V4 Flash actuel.
    "deepseek": {"input": 1.0, "output": 5.0},
}


def in_window(now: datetime) -> bool:
    local = now.astimezone(ZoneInfo("America/Toronto")).time().replace(tzinfo=None)
    return wall_time(0) <= local < wall_time(4)


def conservative_cost(provider: str, usage: dict) -> float:
    if provider == "anthropic":
        weighted_in = usage.get("input_tokens", 0)
        weighted_in += 1.25 * usage.get("cache_creation_input_tokens", 0)
        weighted_in += 0.10 * usage.get("cache_read_input_tokens", 0)
    else:
        weighted_in = usage.get("prompt_cache_miss_tokens", usage.get("input_tokens", 0))
        weighted_in += 0.02 * usage.get("prompt_cache_hit_tokens", 0)
    return (weighted_in * RATES[provider]["input"] + usage.get("output_tokens", 0) * RATES[provider]["output"]) / 1_000_000


class DirectClient:
    def __init__(self, caps: dict[str, float]):
        self.caps = caps
        self.spend = {"anthropic": 0.0, "deepseek": 0.0}
        self.last_meta = None

    def create_message(self, model, messages, max_tokens, temperature, **kwargs):
        if not in_window(datetime.now(timezone.utc)):
            raise RuntimeError("appel refusé hors fenêtre 00:00–04:00 America/Toronto")
        provider, model_id = model.split(":", 1)
        # Réserve le pire cas avant l'appel; le coût réel remplace cette projection après.
        projected = (len(messages[0]["content"]) // 3 + 1000) * RATES[provider]["input"] / 1_000_000
        projected += max_tokens * RATES[provider]["output"] / 1_000_000
        if self.spend[provider] + projected > self.caps[provider]:
            raise RuntimeError(f"budget {provider} refusé avant appel")
        started = time.monotonic()
        if provider == "anthropic":
            from anthropic import Anthropic
            response = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]).messages.create(
                model=model_id, max_tokens=max_tokens, temperature=temperature,
                messages=messages, cache_control={"type": "ephemeral"},
            )
            raw = response.content[0].text
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            }
        else:
            from openai import OpenAI
            response = OpenAI(base_url="https://api.deepseek.com/v1", api_key=os.environ["DEEPSEEK_API_KEY"]).chat.completions.create(
                model=model_id, max_tokens=max_tokens, temperature=temperature,
                messages=messages, extra_body={"thinking": {"type": "disabled"}},
            )
            raw = response.choices[0].message.content
            raw_usage = response.usage.model_dump()
            usage = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
                "prompt_cache_hit_tokens": raw_usage.get("prompt_cache_hit_tokens", 0) or 0,
                "prompt_cache_miss_tokens": raw_usage.get("prompt_cache_miss_tokens", response.usage.prompt_tokens) or 0,
            }
        cost = conservative_cost(provider, usage)
        self.spend[provider] += cost
        self.last_meta = {
            "provider": provider, "model": model_id, "usage": usage,
            "estimated_cost_usd": round(cost, 8),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
        return SimpleNamespace(content=[SimpleNamespace(text=raw)])


def load_corpus() -> str:
    rows = json.loads((ROOT / "corpus/source/corpus_omniroute_pilot.json").read_text(encoding="utf-8"))
    return "\n".join(
        f"Session {r['session_id']}, tour {r['tour_n']}: {r['locuteur']} dit « {r['texte']} »"
        for r in rows
    )


def run(output: Path, repeats: int, interval: float, caps: dict[str, float]) -> int:
    if not in_window(datetime.now(timezone.utc)):
        raise RuntimeError("expérience refusée hors fenêtre autorisée")
    for name in ("ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"):
        if not os.getenv(name):
            raise RuntimeError(f"{name} absent")
    from pipelines.pipeline_p0 import run_p0

    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "protocol": "substrat-bench-P0-direct-pilot-v1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "models": list(MODELS), "repeats": repeats, "caps_usd": caps,
        "authorized_window": "2026-08-10 00:00–04:00 America/Toronto",
        "not_normative_cycle_c": True, "runs": [],
    }
    client = DirectClient(caps)
    for old in manifest["runs"]:
        if old.get("status") == "ok":
            client.spend[old["transport"]["provider"]] += old["transport"]["estimated_cost_usd"]

    corpus = load_corpus()
    for model in MODELS:
        for repeat in range(repeats):
            if any(r["model_requested"] == model and r["repeat"] == repeat and r["status"] == "ok" for r in manifest["runs"]):
                continue
            record = {"model_requested": model, "repeat": repeat}
            try:
                result = run_p0(
                    client=client, model=model, corpus_text=corpus,
                    output_dir=output / model.replace(":", "__") / f"repeat_{repeat}",
                    seed=42 + repeat, max_tokens=1800, temperature=0.0, cycle_num=repeat,
                )
                record.update({
                    "status": "ok", "assertions": [a.to_dict() for a in result.assertions],
                    "raw_output": result.raw_output, "transport": client.last_meta,
                })
            except Exception as error:
                record.update({"status": "error", "error": str(error)})
            record["timestamp"] = datetime.now(timezone.utc).isoformat()
            manifest["runs"].append(record)
            manifest["estimated_spend_usd"] = {k: round(v, 8) for k, v in client.spend.items()}
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(model, repeat, record["status"], manifest["estimated_spend_usd"], flush=True)
            if record["status"] != "ok":
                return 2
            if interval:
                time.sleep(interval)
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/direct_p0_long")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--interval", type=float, default=10)
    parser.add_argument("--anthropic-cap", type=float, default=1.50)
    parser.add_argument("--deepseek-cap", type=float, default=1.50)
    args = parser.parse_args()
    return run(args.output, args.repeats, args.interval, {"anthropic": args.anthropic_cap, "deepseek": args.deepseek_cap})


if __name__ == "__main__":
    raise SystemExit(main())
