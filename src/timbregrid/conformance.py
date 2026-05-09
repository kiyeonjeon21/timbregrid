from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from urllib.parse import urljoin

import httpx


Expectation = Literal["success", "error", "stream_or_error"]


@dataclass(frozen=True)
class ConformanceCase:
    name: str
    payload: dict
    expectation: Expectation


@dataclass(frozen=True)
class ConformanceCaseResult:
    name: str
    passed: bool
    expectation: Expectation
    request_payload: dict
    status_code: int | None
    content_type: str | None
    content_length: int
    elapsed_ms: float
    response_kind: str | None = None
    error_type: str | None = None
    error_code: str | None = None
    failure: str | None = None


@dataclass(frozen=True)
class ConformanceReport:
    schema_version: str
    created_at: str
    base_url: str
    endpoint: str
    config: dict
    summary: dict
    cases: list[ConformanceCaseResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.summary["failed"] == 0

    @property
    def passed(self) -> int:
        return self.summary["passed"]

    @property
    def failed(self) -> int:
        return self.summary["failed"]

    @property
    def failures(self) -> list[str]:
        return [
            f"{case.name}: {case.failure}"
            for case in self.cases
            if not case.passed and case.failure is not None
        ]

    def to_dict(self) -> dict:
        return asdict(self)


def build_speech_cases(
    *,
    model: str = "fake:tts",
    voice: str = "alloy",
    response_format: str = "wav",
) -> list[ConformanceCase]:
    base = {
        "model": model,
        "input": "Hello from the TimbreGrid speech conformance suite.",
        "voice": voice,
        "response_format": response_format,
    }
    return [
        ConformanceCase(
            name="required fields with response_format",
            payload=base,
            expectation="success",
        ),
        ConformanceCase(
            name="speed field",
            payload={**base, "speed": 1.1},
            expectation="success",
        ),
        ConformanceCase(
            name="instructions field",
            payload={**base, "instructions": "Speak clearly."},
            expectation="success",
        ),
        ConformanceCase(
            name="missing model",
            payload={"input": base["input"], "voice": voice, "response_format": response_format},
            expectation="error",
        ),
        ConformanceCase(
            name="missing input",
            payload={"model": model, "voice": voice, "response_format": response_format},
            expectation="error",
        ),
        ConformanceCase(
            name="missing voice",
            payload={"model": model, "input": base["input"], "response_format": response_format},
            expectation="error",
        ),
        ConformanceCase(
            name="invalid speed low",
            payload={**base, "speed": 0.1},
            expectation="error",
        ),
        ConformanceCase(
            name="invalid speed high",
            payload={**base, "speed": 4.1},
            expectation="error",
        ),
        ConformanceCase(
            name="unknown model",
            payload={**base, "model": "__timbregrid_unknown_model__"},
            expectation="error",
        ),
        ConformanceCase(
            name="unsupported response_format",
            payload={**base, "response_format": "__timbregrid_invalid_format__"},
            expectation="error",
        ),
        ConformanceCase(
            name="sse stream_format",
            payload={**base, "stream_format": "sse"},
            expectation="stream_or_error",
        ),
    ]


def run_conformance(
    base_url: str,
    *,
    endpoint: str = "audio.speech",
    model: str = "fake:tts",
    voice: str = "alloy",
    response_format: str = "wav",
    timeout: float = 10.0,
) -> ConformanceReport:
    if endpoint != "audio.speech":
        raise ValueError("Only endpoint='audio.speech' is supported in the MVP")

    cases = build_speech_cases(model=model, voice=voice, response_format=response_format)
    url = urljoin(base_url.rstrip("/") + "/", "audio/speech")
    results: list[ConformanceCaseResult] = []

    with httpx.Client(timeout=timeout) as client:
        for case in cases:
            started = time.perf_counter()
            try:
                response = client.post(url, json=case.payload)
                elapsed_ms = (time.perf_counter() - started) * 1000
                results.append(_evaluate_response(case, response, elapsed_ms))
            except httpx.HTTPError as exc:
                elapsed_ms = (time.perf_counter() - started) * 1000
                results.append(
                    ConformanceCaseResult(
                        name=case.name,
                        passed=False,
                        expectation=case.expectation,
                        request_payload=case.payload,
                        status_code=None,
                        content_type=None,
                        content_length=0,
                        elapsed_ms=elapsed_ms,
                        failure=str(exc),
                    )
                )

    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    return ConformanceReport(
        schema_version="0.1",
        created_at=datetime.now(timezone.utc).isoformat(),
        base_url=base_url,
        endpoint=endpoint,
        config={
            "model": model,
            "voice": voice,
            "response_format": response_format,
            "timeout": timeout,
        },
        summary={
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "failure_rate": failed / len(results) if results else 0.0,
        },
        cases=results,
    )


def write_conformance_report(report: ConformanceReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _evaluate_response(
    case: ConformanceCase,
    response: httpx.Response,
    elapsed_ms: float,
) -> ConformanceCaseResult:
    content_type = response.headers.get("content-type", "")
    content_length = len(response.content)
    error_type, error_code = _extract_openai_error(response)
    response_kind = _response_kind(response, content_type)
    failure = _failure_reason(
        case.expectation,
        status_code=response.status_code,
        content_type=content_type,
        content_length=content_length,
        error_type=error_type,
    )

    return ConformanceCaseResult(
        name=case.name,
        passed=failure is None,
        expectation=case.expectation,
        request_payload=case.payload,
        status_code=response.status_code,
        content_type=content_type or None,
        content_length=content_length,
        elapsed_ms=elapsed_ms,
        response_kind=response_kind,
        error_type=error_type,
        error_code=error_code,
        failure=failure,
    )


def _failure_reason(
    expectation: Expectation,
    *,
    status_code: int,
    content_type: str,
    content_length: int,
    error_type: str | None,
) -> str | None:
    if expectation == "success":
        if status_code != 200:
            return f"expected HTTP 200, got {status_code}"
        if content_length == 0:
            return "expected non-empty audio bytes"
        if not _is_audio_content_type(content_type):
            return f"expected audio content type, got {content_type!r}"
        return None

    if expectation == "error":
        if 200 <= status_code < 300:
            return f"expected non-2xx error, got {status_code}"
        if "application/json" not in content_type:
            return f"expected JSON error response, got {content_type!r}"
        if error_type is None:
            return "expected OpenAI-shaped error body"
        return None

    if status_code == 200:
        if "text/event-stream" not in content_type:
            return f"expected text/event-stream for SSE success, got {content_type!r}"
        return None

    if "application/json" not in content_type:
        return f"expected JSON error response for unsupported SSE, got {content_type!r}"
    if error_type is None:
        return "expected OpenAI-shaped error body for unsupported SSE"
    return None


def _is_audio_content_type(content_type: str) -> bool:
    return content_type.startswith("audio/") or "application/octet-stream" in content_type


def _response_kind(response: httpx.Response, content_type: str) -> str:
    if response.status_code == 200 and "text/event-stream" in content_type:
        return "sse"
    if response.status_code == 200 and _is_audio_content_type(content_type):
        return "audio"
    if "application/json" in content_type:
        return "json"
    return "other"


def _extract_openai_error(response: httpx.Response) -> tuple[str | None, str | None]:
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return None, None

    try:
        body = response.json()
    except ValueError:
        return None, None

    error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict):
        return None, None

    error_type = error.get("type")
    error_code = error.get("code")
    return (
        error_type if isinstance(error_type, str) else None,
        error_code if isinstance(error_code, str) else None,
    )
