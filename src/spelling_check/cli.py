from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import cast

from spelling_check.client import VllmClient
from spelling_check.models import CorrectionResult
from spelling_check.pipeline import SpellingCheckConfig, spelling_check

DEFAULT_BASE_URL = "http://localhost:8000/v1"
DEFAULT_MODEL = "google/gemma-4-E4B"
DEFAULT_SAMPLE_FILE = Path(__file__).resolve().parents[2] / "data" / "sample_sentences.json"


def main() -> int:
    args = parse_args()
    client = VllmClient(
        base_url=args.base_url,
        model=args.model,
        api_key=args.api_key,
        timeout=args.timeout,
    )
    config = SpellingCheckConfig(
        prompt_logprobs=args.prompt_logprobs,
        risk_threshold=args.risk_threshold,
        suspicious_limit=args.suspicious_limit,
        candidate_limit=args.candidate_limit,
        window_radius=args.window_radius,
        strong_delta=args.strong_delta,
        weak_delta=args.weak_delta,
        margin=args.margin,
    )

    for text in load_inputs(args):
        result = spelling_check(text, client, config)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False))
        else:
            print_human(result)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chinese spelling check POC using vLLM prompt logprobs.")
    parser.add_argument("texts", nargs="*", help="input sentences")
    parser.add_argument("--input-file", type=Path, help="JSON array or newline-delimited text input")
    parser.add_argument("--use-samples", action="store_true", help="run data/sample_sentences.json")
    parser.add_argument("--base-url", default=os.getenv("SPELLING_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--model", default=os.getenv("SPELLING_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-key", default=os.getenv("SPELLING_API_KEY"))
    parser.add_argument("--timeout", type=float, default=float(os.getenv("SPELLING_TIMEOUT", "30")))
    parser.add_argument("--prompt-logprobs", type=int, default=5)
    parser.add_argument("--risk-threshold", type=float, default=7.0)
    parser.add_argument("--suspicious-limit", type=int, default=5)
    parser.add_argument("--candidate-limit", type=int, default=8)
    parser.add_argument("--window-radius", type=int, default=12)
    parser.add_argument("--strong-delta", type=float, default=1.0)
    parser.add_argument("--weak-delta", type=float, default=0.3)
    parser.add_argument("--margin", type=float, default=0.4)
    parser.add_argument("--json", action="store_true", help="print JSON lines")
    return parser.parse_args()


def load_inputs(args: argparse.Namespace) -> list[str]:
    texts = cast("list[str]", args.texts)
    if texts:
        return texts
    if args.input_file:
        return _load_file(args.input_file)
    if args.use_samples:
        return _load_file(DEFAULT_SAMPLE_FILE)
    raise SystemExit("請提供句子、--input-file，或 --use-samples。")


def _load_file(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(raw)
        return [str(item) for item in data]
    return [line.strip() for line in raw.splitlines() if line.strip()]


def print_human(result: CorrectionResult) -> None:
    print(f"\n輸入: {result.input}")
    print(f"狀態: {result.status} / confidence={result.confidence}")
    if result.corrected_text:
        print(f"修正: {result.corrected_text}")

    if result.corrections:
        print("候選:")
        for correction in result.corrections:
            print(
                "  "
                f"{correction.index}: {correction.original_char} -> {correction.candidate_char} "
                f"delta={correction.delta:.4f} source={correction.source}"
            )

    if result.suspicious_chars:
        print("疑似錯字:")
        for risk in result.suspicious_chars:
            print(f"  {risk.index}: {risk.char} risk={risk.risk_score:.4f} ({risk.reason})")


if __name__ == "__main__":
    raise SystemExit(main())
