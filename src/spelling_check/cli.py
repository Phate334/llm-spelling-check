from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from spelling_check.client import VllmClient
from spelling_check.dataset import SgmlDataset, load_sgml_dataset, load_texts
from spelling_check.evaluation import evaluate_csc
from spelling_check.models import CorrectionResult
from spelling_check.pipeline import SpellingCheckConfig, spelling_check
from spelling_check.settings import load_env_settings

DEFAULT_SAMPLE_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "sample_sentences.json"
)


def main() -> int:
    args = parse_args()
    if args.input_file and args.input_file.suffix.lower() == ".sgml":
        if args.texts:
            raise SystemExit(
                "SGML input file cannot be combined with positional texts."
            )
        return run_sgml_evaluation(args)

    client = _build_client(args)
    config = _build_config(args)

    for text in load_inputs(args):
        result = spelling_check(text, client, config)
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False))
        else:
            print_human(result)
    return 0


def parse_args() -> argparse.Namespace:
    env_settings = load_env_settings()
    parser = argparse.ArgumentParser(
        description="Chinese spelling check POC using vLLM prompt logprobs."
    )
    parser.add_argument("texts", nargs="*", help="input sentences")
    parser.add_argument(
        "--input-file",
        type=Path,
        help="JSON array, newline-delimited text, or SGML evaluation input",
    )
    parser.add_argument(
        "--use-samples",
        action="store_true",
        help="run local data/sample_sentences.json if you placed it there",
    )
    parser.add_argument("--base-url", default=env_settings.base_url)
    parser.add_argument("--model", default=env_settings.model)
    parser.add_argument("--api-key", default=env_settings.normalized_api_key)
    parser.add_argument("--timeout", type=float, default=env_settings.timeout)
    parser.add_argument("--prompt-logprobs", type=int, default=5)
    parser.add_argument("--risk-threshold", type=float, default=7.0)
    parser.add_argument("--suspicious-limit", type=int, default=5)
    parser.add_argument("--candidate-limit", type=int, default=8)
    parser.add_argument("--window-radius", type=int, default=12)
    parser.add_argument("--score-batch-size", type=int, default=1)
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
        return load_texts(args.input_file)
    if args.use_samples:
        if not DEFAULT_SAMPLE_FILE.is_file():
            raise SystemExit(
                "找不到 data/sample_sentences.json。repo 已不再內建 sample data，"
                "請先把檔案放到 data/，或改用 --input-file。"
            )
        return load_texts(DEFAULT_SAMPLE_FILE)
    raise SystemExit("請提供句子、--input-file，或 --use-samples。")


def run_sgml_evaluation(args: argparse.Namespace) -> int:
    dataset = load_sgml_dataset(args.input_file)
    client = _build_client(args)
    config = _build_config(args)
    results = [
        spelling_check(case.input_text, client=client, config=config)
        for case in dataset.cases
    ]
    metrics = evaluate_csc(results, [case.gold_text for case in dataset.cases])
    print(
        json.dumps(
            _sgml_output(dataset, results, metrics.to_dict()), ensure_ascii=False
        )
    )
    return 0


def _build_client(args: argparse.Namespace) -> VllmClient:
    return VllmClient(
        base_url=args.base_url,
        model=args.model,
        api_key=args.api_key,
        timeout=args.timeout,
    )


def _build_config(args: argparse.Namespace) -> SpellingCheckConfig:
    return SpellingCheckConfig(
        prompt_logprobs=args.prompt_logprobs,
        risk_threshold=args.risk_threshold,
        suspicious_limit=args.suspicious_limit,
        candidate_limit=args.candidate_limit,
        window_radius=args.window_radius,
        score_batch_size=args.score_batch_size,
        strong_delta=args.strong_delta,
        weak_delta=args.weak_delta,
        margin=args.margin,
    )


def _sgml_output(
    dataset: SgmlDataset,
    results: list[CorrectionResult],
    metrics: dict[str, float | int],
) -> dict[str, object]:
    return {
        "dataset": {
            "path": str(dataset.path),
            "format": "sgml",
            "case_count": len(dataset.cases),
            "gold_error_count": dataset.gold_error_count,
        },
        "metrics": metrics,
        "cases": [
            _sgml_case_output(case.case_id, case.input_text, case.gold_text, result)
            for case, result in zip(dataset.cases, results, strict=True)
        ],
    }


def _sgml_case_output(
    case_id: str, input_text: str, gold_text: str, result: CorrectionResult
) -> dict[str, object]:
    result_data = result.to_dict()
    return {
        "id": case_id,
        "input": input_text,
        "gold": gold_text,
        "status": result_data["status"],
        "corrected_text": result_data["corrected_text"],
        "suspicious_chars": result_data["suspicious_chars"],
        "corrections": result_data["corrections"],
    }


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
            print(
                f"  {risk.index}: {risk.char} risk={risk.risk_score:.4f} ({risk.reason})"
            )


if __name__ == "__main__":
    raise SystemExit(main())
