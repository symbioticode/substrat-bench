#!/usr/bin/env python3
"""Pilote réel P0 sur deux providers Omniroute, sans dépendance Python externe."""

import argparse
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def parse_sse(body: str) -> str:
    """Reconstruit le contenu OpenAI depuis un flux SSE Omniroute."""
    chunks = []
    for line in body.splitlines():
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        event = json.loads(payload)
        choice = (event.get("choices") or [{}])[0]
        text = (choice.get("delta") or {}).get("content")
        if text is None:
            text = (choice.get("message") or {}).get("content")
        if text:
            chunks.append(text)
    return "".join(chunks)


def extract_content(body: str, content_type: str) -> str:
    if "text/event-stream" in content_type or body.lstrip().startswith("data:"):
        return parse_sse(body)
    data = json.loads(body)
    return data["choices"][0]["message"]["content"]


@dataclass
class CallMeta:
    provider: str
    routed_model: str
    cache: str
    cost: str
    tokens_in: str
    tokens_out: str
    content_type: str


class OmnirouteClient:
    def __init__(self, base_url: str, timeout: int = 120):
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.timeout = timeout
        self.last_meta = None

    def create_message(self, model, messages, max_tokens, temperature, **kwargs):
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }).encode()
        request = urllib.request.Request(self.url, data=payload, headers={
            "Content-Type": "application/json",
            "x-omniroute-no-cache": "true",
            "x-omniroute-no-memory": "true",
        })
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                headers = response.headers
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Omniroute HTTP {error.code}: {detail[:500]}") from error
        content_type = headers.get("content-type", "")
        self.last_meta = CallMeta(
            provider=headers.get("x-omniroute-provider", "unknown"),
            routed_model=headers.get("x-omniroute-model", "unknown"),
            cache=headers.get("x-omniroute-cache", "unknown"),
            cost=headers.get("x-omniroute-response-cost", "unknown"),
            tokens_in=headers.get("x-omniroute-tokens-in", "unknown"),
            tokens_out=headers.get("x-omniroute-tokens-out", "unknown"),
            content_type=content_type,
        )
        text = extract_content(body, content_type)
        return SimpleNamespace(content=[SimpleNamespace(text=text)])


def load_corpus() -> str:
    rows = json.loads((ROOT / "corpus/source/corpus_omniroute_pilot.json").read_text())
    return "\n".join(
        f"Session {r['session_id']}, tour {r['tour_n']}: {r['locuteur']} dit « {r['texte']} »"
        for r in rows
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="groq/llama-3.3-70b-versatile,mistral/mistral-small-latest")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--interval", type=float, default=15.0)
    parser.add_argument("--base-url", default="http://localhost:20128/v1")
    parser.add_argument("--output", default="results/omniroute_p0_pilot")
    args = parser.parse_args()

    from pipelines.pipeline_p0 import run_p0

    output = ROOT / args.output
    output.mkdir(parents=True, exist_ok=True)
    corpus = load_corpus()
    client = OmnirouteClient(args.base_url)
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "runs": []}

    for model in args.models.split(","):
        for repeat in range(args.repeats):
            started = time.perf_counter()
            record = {"model_requested": model, "repeat": repeat}
            try:
                result = run_p0(
                    client=client, model=model, corpus_text=corpus,
                    output_dir=output / model.replace("/", "__") / f"repeat_{repeat}",
                    seed=42 + repeat, max_tokens=1800, temperature=0.0,
                    cycle_num=repeat,
                )
                record.update({
                    "status": "ok", "assertions": [a.to_dict() for a in result.assertions],
                    "raw_output": result.raw_output, "transport": vars(client.last_meta),
                })
            except Exception as error:
                record.update({"status": "error", "error": str(error)})
            record["elapsed_seconds"] = round(time.perf_counter() - started, 3)
            record["timestamp"] = datetime.now(timezone.utc).isoformat()
            manifest["runs"].append(record)
            (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
            print(model, repeat, record["status"], record.get("elapsed_seconds"))
            if args.interval and not (model == args.models.split(",")[-1] and repeat == args.repeats - 1):
                time.sleep(args.interval)

    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
