from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, cast

from spelling_check.alignment import align_tokens_to_chars
from spelling_check.candidates import generate_candidates
from spelling_check.client import VllmClient
from spelling_check.dataset import parse_sgml_dataset
from spelling_check.evaluation import evaluate_csc
from spelling_check.models import (
    Candidate,
    CandidateCorrection,
    CharRisk,
    CorrectionResult,
)
from spelling_check.pipeline import PromptScorer, SpellingCheckConfig, spelling_check
from spelling_check.risk import compute_char_risks, select_suspicious_chars
from spelling_check.settings import load_env_settings


class ClientFactory(Protocol):
    def __call__(self, settings: ModelSettings) -> PromptScorer: ...


@dataclass(frozen=True)
class NormalizedCase:
    id: str
    input: str
    gold: str | None
    source_format: str


@dataclass(frozen=True)
class ModelSettings:
    base_url: str
    model: str
    api_key: str | None
    timeout: float
    config: SpellingCheckConfig

    def public_dict(self) -> dict[str, object]:
        return {
            "base_url": self.base_url,
            "model": self.model,
            "timeout": self.timeout,
            "config": asdict(self.config),
        }


def default_settings(data: dict[str, Any] | None = None) -> ModelSettings:
    data = data or {}
    env_settings = load_env_settings()
    raw_config = data.get("config")
    config_data: dict[str, Any] = raw_config if isinstance(raw_config, dict) else {}
    api_key = data.get("api_key") or env_settings.normalized_api_key
    return ModelSettings(
        base_url=str(data.get("base_url") or env_settings.base_url),
        model=str(data.get("model") or env_settings.model),
        api_key=str(api_key) if api_key else None,
        timeout=float(data.get("timeout") or env_settings.timeout),
        config=SpellingCheckConfig(
            prompt_logprobs=int(config_data.get("prompt_logprobs", 5)),
            risk_threshold=float(config_data.get("risk_threshold", 7.0)),
            suspicious_limit=int(config_data.get("suspicious_limit", 5)),
            candidate_limit=int(config_data.get("candidate_limit", 8)),
            window_radius=int(config_data.get("window_radius", 12)),
            score_batch_size=int(config_data.get("score_batch_size", 1)),
            strong_delta=float(config_data.get("strong_delta", 1.0)),
            weak_delta=float(config_data.get("weak_delta", 0.3)),
            margin=float(config_data.get("margin", 0.4)),
        ),
    )


def default_client_factory(settings: ModelSettings) -> VllmClient:
    return VllmClient(
        base_url=settings.base_url,
        model=settings.model,
        api_key=settings.api_key,
        timeout=settings.timeout,
    )


def parse_cases(
    *,
    text: str | None = None,
    file_name: str | None = None,
    file_content: bytes | None = None,
) -> list[NormalizedCase]:
    if file_content is not None:
        raw = file_content.decode("utf-8")
        suffix = Path(file_name or "").suffix.lower()
        if suffix == ".sgml":
            dataset = parse_sgml_dataset(raw, path=Path(file_name or "<upload>"))
            return [
                NormalizedCase(
                    id=case.case_id,
                    input=case.input_text,
                    gold=case.gold_text,
                    source_format="sgml",
                )
                for case in dataset.cases
            ]
        if suffix == ".json":
            return _parse_json_cases(raw)
        return _parse_text_cases(raw, source_format="text")

    return _parse_text_cases(text or "", source_format="text")


def detect_cases(
    cases: list[NormalizedCase],
    settings: ModelSettings,
    client_factory: ClientFactory = default_client_factory,
) -> list[dict[str, object]]:
    client = client_factory(settings)
    detected = []
    for case in cases:
        response = client.score_prompt(case.input, settings.config.prompt_logprobs)
        tokens = align_tokens_to_chars(case.input, response)
        risks = compute_char_risks(case.input, tokens)
        suspicious = select_suspicious_chars(
            risks,
            threshold=settings.config.risk_threshold,
            limit=settings.config.suspicious_limit,
        )
        candidates: list[Candidate] = []
        for risk in suspicious:
            candidates.extend(
                generate_candidates(risk, tokens, settings.config.candidate_limit)
            )
        detected.append(
            {
                **_case_dict(case),
                "suspicious_chars": [_risk_dict(risk) for risk in suspicious],
                "candidate_count": len(candidates),
            }
        )
    return detected


def correct_cases(
    cases: list[NormalizedCase],
    settings: ModelSettings,
    client_factory: ClientFactory = default_client_factory,
) -> list[dict[str, object]]:
    client = client_factory(settings)
    return [
        _result_case_dict(
            case,
            spelling_check(case.input, client=client, config=settings.config),
        )
        for case in cases
    ]


def evaluate_case_results(cases: list[dict[str, object]]) -> dict[str, object] | None:
    if not cases or any(case.get("gold") is None for case in cases):
        return None
    results = [_result_from_case(case) for case in cases]
    gold_texts = [str(case["gold"]) for case in cases]
    return cast("dict[str, object]", evaluate_csc(results, gold_texts).to_dict())


def run_all(
    *,
    text: str | None = None,
    file_name: str | None = None,
    file_content: bytes | None = None,
    settings_data: dict[str, Any] | None = None,
    client_factory: ClientFactory = default_client_factory,
) -> dict[str, object]:
    settings = default_settings(settings_data)
    cases = parse_cases(text=text, file_name=file_name, file_content=file_content)
    result_cases = correct_cases(cases, settings, client_factory)
    metrics = evaluate_case_results(result_cases)
    return {
        "settings": settings.public_dict(),
        "summary": _summary(result_cases),
        "metrics": metrics,
        "cases": result_cases,
    }


def _parse_json_cases(raw: str) -> list[NormalizedCase]:
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("JSON input must be an array")
    cases: list[NormalizedCase] = []
    for index, item in enumerate(data, start=1):
        if isinstance(item, str):
            cases.append(
                NormalizedCase(
                    id=f"json-{index}",
                    input=item,
                    gold=None,
                    source_format="json",
                )
            )
        elif isinstance(item, dict):
            cases.append(
                NormalizedCase(
                    id=str(item.get("id") or f"json-{index}"),
                    input=str(item["input"]),
                    gold=str(item["gold"]) if item.get("gold") is not None else None,
                    source_format="json",
                )
            )
        else:
            raise ValueError("JSON items must be strings or objects")
    return cases


def _parse_text_cases(raw: str, source_format: str) -> list[NormalizedCase]:
    return [
        NormalizedCase(
            id=f"text-{index}",
            input=line.strip(),
            gold=None,
            source_format=source_format,
        )
        for index, line in enumerate(raw.splitlines(), start=1)
        if line.strip()
    ]


def _case_dict(case: NormalizedCase) -> dict[str, object]:
    return {
        "id": case.id,
        "input": case.input,
        "gold": case.gold,
        "source_format": case.source_format,
    }


def _risk_dict(risk: CharRisk) -> dict[str, object]:
    return {
        "index": risk.index,
        "char": risk.char,
        "risk_score": risk.risk_score,
        "token_logprob": risk.token_logprob,
        "span_score": risk.span_score,
        "reason": risk.reason,
    }


def _result_case_dict(
    case: NormalizedCase, result: CorrectionResult
) -> dict[str, object]:
    result_data = result.to_dict()
    return {
        **_case_dict(case),
        "status": result.status,
        "corrected_text": result.corrected_text,
        "confidence": result.confidence,
        "suspicious_chars": result_data["suspicious_chars"],
        "corrections": result_data["corrections"],
    }


def _result_from_case(case: dict[str, object]) -> CorrectionResult:
    suspicious_raw = _list_of_dicts(case.get("suspicious_chars"))
    corrections_raw = _list_of_dicts(case.get("corrections"))
    corrected_text = case.get("corrected_text")
    return CorrectionResult(
        input=str(case["input"]),
        status=str(case["status"]),
        confidence=str(case.get("confidence") or ""),
        corrected_text=corrected_text if isinstance(corrected_text, str) else None,
        suspicious_chars=[_risk_from_dict(item) for item in suspicious_raw],
        corrections=[_correction_from_dict(item) for item in corrections_raw],
    )


def _summary(cases: list[dict[str, object]]) -> dict[str, int]:
    status_counts = {
        status: sum(1 for case in cases if case.get("status") == status)
        for status in ("corrected", "uncertain", "no_error")
    }
    return {
        "case_count": len(cases),
        **status_counts,
        "suspicious_count": sum(
            _list_length(case.get("suspicious_chars")) for case in cases
        ),
        "candidate_count": sum(_list_length(case.get("corrections")) for case in cases),
    }


def _list_of_dicts(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [cast("dict[str, object]", item) for item in value if isinstance(item, dict)]


def _list_length(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _risk_from_dict(data: dict[str, object]) -> CharRisk:
    return CharRisk(
        index=int(str(data["index"])),
        char=str(data["char"]),
        risk_score=float(str(data["risk_score"])),
        token_logprob=_optional_float(data.get("token_logprob")),
        span_score=_optional_float(data.get("span_score")),
        reason=str(data["reason"]),
    )


def _correction_from_dict(data: dict[str, object]) -> CandidateCorrection:
    return CandidateCorrection(
        index=int(str(data["index"])),
        original_char=str(data["original_char"]),
        candidate_char=str(data["candidate_char"]),
        source=str(data["source"]),
        original_text=str(data["original_text"]),
        candidate_text=str(data["candidate_text"]),
        original_score=float(str(data["original_score"])),
        candidate_score=float(str(data["candidate_score"])),
        delta=float(str(data["delta"])),
        original_span=str(data["original_span"]),
        corrected_span=str(data["corrected_span"]),
    )


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(str(value))
