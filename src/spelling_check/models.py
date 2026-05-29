from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class TokenScore:
    token_id: int | None
    token_text: str
    start: int
    end: int
    logprob: float
    top_logprobs: list[dict[str, object]] = field(default_factory=list)


@dataclass
class CharRisk:
    index: int
    char: str
    risk_score: float
    token_logprob: float | None
    span_score: float | None
    reason: str


@dataclass
class Candidate:
    index: int
    original_char: str
    candidate_char: str
    source: str
    original_span: str
    corrected_span: str


@dataclass
class CandidateCorrection:
    index: int
    original_char: str
    candidate_char: str
    source: str
    original_text: str
    candidate_text: str
    original_score: float
    candidate_score: float
    delta: float
    original_span: str
    corrected_span: str


@dataclass
class CorrectionResult:
    input: str
    status: str
    confidence: str
    corrected_text: str | None
    corrections: list[CandidateCorrection]
    suspicious_chars: list[CharRisk]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
