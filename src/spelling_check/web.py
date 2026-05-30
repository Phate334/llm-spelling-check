from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.datastructures import UploadFile as StarletteUploadFile

from spelling_check.service import (
    ClientFactory,
    ModelSettings,
    NormalizedCase,
    correct_cases,
    default_client_factory,
    default_settings,
    detect_cases,
    evaluate_case_results,
    parse_cases,
    run_all,
)

STATIC_DIR = Path(__file__).with_name("static")
INDEX_FILE = STATIC_DIR / "index.html"


def create_app(
    client_factory: ClientFactory = default_client_factory,
) -> FastAPI:
    app = FastAPI(title="LLM Spelling Check", version="0.2.5")
    app.state.client_factory = client_factory
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(INDEX_FILE.read_text(encoding="utf-8"))

    @app.get("/api/defaults")
    async def api_defaults() -> dict[str, object]:
        return {"settings": default_settings({}).public_dict()}

    @app.post("/api/parse")
    async def api_parse(request: Request) -> dict[str, object]:
        payload = await _read_input(request)
        try:
            cases = _parse_from_payload(payload)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"cases": [_normalized_case_dict(case) for case in cases]}

    @app.post("/api/detect")
    async def api_detect(request: Request) -> dict[str, object]:
        payload = await _read_input(request)
        settings = _settings_from_payload(payload)
        cases = _cases_from_payload(payload)
        return {
            "settings": settings.public_dict(),
            "cases": detect_cases(cases, settings, request.app.state.client_factory),
        }

    @app.post("/api/correct")
    async def api_correct(request: Request) -> dict[str, object]:
        payload = await _read_input(request)
        settings = _settings_from_payload(payload)
        cases = _cases_from_payload(payload)
        result_cases = correct_cases(
            cases,
            settings,
            request.app.state.client_factory,
        )
        return {
            "settings": settings.public_dict(),
            "summary": _summary_from_cases(result_cases),
            "metrics": evaluate_case_results(result_cases),
            "cases": result_cases,
        }

    @app.post("/api/evaluate")
    async def api_evaluate(request: Request) -> dict[str, object]:
        payload = await _read_input(request)
        cases = payload.get("cases")
        if not isinstance(cases, list):
            raise HTTPException(status_code=400, detail="cases must be an array")
        metrics = evaluate_case_results(_dict_cases(cases))
        return {"metrics": metrics}

    @app.post("/api/run")
    async def api_run(request: Request) -> dict[str, object]:
        payload = await _read_input(request)
        try:
            return run_all(
                text=_optional_str(payload.get("text")),
                file_name=_optional_str(payload.get("file_name")),
                file_content=_optional_bytes(payload.get("file_content")),
                settings_data=_settings_data(payload),
                client_factory=request.app.state.client_factory,
            )
        except (
            KeyError,
            TypeError,
            ValueError,
            RuntimeError,
            json.JSONDecodeError,
        ) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return app


app = create_app()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the spelling check WebUI.")
    parser.add_argument("--host", default=os.getenv("SPELLING_WEB_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.getenv("SPELLING_WEB_PORT", "8000"))
    )
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(
        "spelling_check.web:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


async def _read_input(request: Request) -> dict[str, object]:
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        payload: dict[str, object] = {}
        if "text" in form:
            payload["text"] = str(form["text"])
        if "settings" in form and str(form["settings"]).strip():
            payload["settings"] = json.loads(str(form["settings"]))
        upload = form.get("file")
        if isinstance(upload, StarletteUploadFile):
            payload["file_name"] = upload.filename or "upload.txt"
            payload["file_content"] = await upload.read()
        return payload

    body = await request.body()
    if not body:
        return {}
    data = json.loads(body.decode("utf-8"))
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="request body must be an object")
    return data


def _settings_from_payload(payload: dict[str, object]) -> ModelSettings:
    return default_settings(_settings_data(payload))


def _settings_data(payload: dict[str, object]) -> dict[str, Any]:
    settings = payload.get("settings")
    if isinstance(settings, dict):
        return settings
    return payload


def _parse_from_payload(payload: dict[str, object]) -> list[NormalizedCase]:
    if isinstance(payload.get("cases"), list):
        return _normalized_cases(payload["cases"])
    return parse_cases(
        text=_optional_str(payload.get("text")),
        file_name=_optional_str(payload.get("file_name")),
        file_content=_optional_bytes(payload.get("file_content")),
    )


def _cases_from_payload(payload: dict[str, object]) -> list[NormalizedCase]:
    cases = payload.get("cases")
    if isinstance(cases, list):
        return _normalized_cases(cases)
    return _parse_from_payload(payload)


def _normalized_cases(raw_cases: object) -> list[NormalizedCase]:
    if not isinstance(raw_cases, list):
        raise ValueError("cases must be an array")
    cases: list[NormalizedCase] = []
    for index, item in enumerate(raw_cases, start=1):
        if not isinstance(item, dict):
            raise ValueError("cases items must be objects")
        cases.append(
            NormalizedCase(
                id=str(item.get("id") or f"case-{index}"),
                input=str(item["input"]),
                gold=str(item["gold"]) if item.get("gold") is not None else None,
                source_format=str(item.get("source_format") or "text"),
            )
        )
    return cases


def _dict_cases(raw_cases: object) -> list[dict[str, object]]:
    if not isinstance(raw_cases, list):
        raise ValueError("cases must be an array")
    return [case for case in raw_cases if isinstance(case, dict)]


def _normalized_case_dict(case: NormalizedCase) -> dict[str, object]:
    return asdict(case)


def _summary_from_cases(cases: list[dict[str, object]]) -> dict[str, int]:
    return {
        "case_count": len(cases),
        "corrected": sum(1 for case in cases if case.get("status") == "corrected"),
        "uncertain": sum(1 for case in cases if case.get("status") == "uncertain"),
        "no_error": sum(1 for case in cases if case.get("status") == "no_error"),
        "suspicious_count": sum(
            _list_length(case.get("suspicious_chars")) for case in cases
        ),
        "candidate_count": sum(_list_length(case.get("corrections")) for case in cases),
    }


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_bytes(value: object) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    raise TypeError("file_content must be bytes")


def _list_length(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


if __name__ == "__main__":
    raise SystemExit(main())
