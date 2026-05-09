from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from timbregrid.conformance import ConformanceCaseResult, ConformanceReport, run_conformance


ReadinessStatus = Literal["ready", "likely_ready", "failed"]


@dataclass(frozen=True)
class IntegrationReadiness:
    status: ReadinessStatus
    reason: str
    cases: list[str]


@dataclass(frozen=True)
class DoctorReport:
    schema_version: str
    created_at: str
    base_url: str
    endpoint: str
    model: str
    voice: str
    response_format: str
    summary: dict
    conformance: ConformanceReport
    integration_readiness: dict[str, IntegrationReadiness]

    @property
    def ok(self) -> bool:
        return bool(self.summary["ok"])

    def to_dict(self) -> dict:
        return asdict(self)


def run_doctor(
    base_url: str,
    *,
    endpoint: str = "audio.speech",
    model: str = "fake:tts",
    voice: str = "alloy",
    response_format: str = "wav",
    timeout: float = 10.0,
) -> DoctorReport:
    conformance = run_conformance(
        base_url,
        endpoint=endpoint,
        model=model,
        voice=voice,
        response_format=response_format,
        timeout=timeout,
    )
    return build_doctor_report(conformance)


def build_doctor_report(conformance: ConformanceReport) -> DoctorReport:
    return DoctorReport(
        schema_version="0.1",
        created_at=datetime.now(timezone.utc).isoformat(),
        base_url=conformance.base_url,
        endpoint=conformance.endpoint,
        model=conformance.config["model"],
        voice=conformance.config["voice"],
        response_format=conformance.config["response_format"],
        summary={
            "ok": conformance.ok,
            "total": conformance.summary["total"],
            "passed": conformance.summary["passed"],
            "failed": conformance.summary["failed"],
            "failure_rate": conformance.summary["failure_rate"],
        },
        conformance=conformance,
        integration_readiness=_integration_readiness(conformance),
    )


def write_doctor_report(report: DoctorReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _integration_readiness(report: ConformanceReport) -> dict[str, IntegrationReadiness]:
    required = _case(report, "required fields with response_format")
    speed = _case(report, "speed field")
    instructions = _case(report, "instructions field")

    open_webui = _open_webui_readiness(required)
    pipecat = _pipecat_readiness(required, speed, instructions)
    return {
        "open_webui_tts": open_webui,
        "pipecat_openai_tts": pipecat,
    }


def _open_webui_readiness(case: ConformanceCaseResult | None) -> IntegrationReadiness:
    if _audio_success(case):
        return IntegrationReadiness(
            status="ready",
            reason="basic OpenAI-compatible /v1/audio/speech request returned audio",
            cases=["required fields with response_format"],
        )
    return IntegrationReadiness(
        status="failed",
        reason=_case_failure(case, "basic speech request did not return audio"),
        cases=["required fields with response_format"],
    )


def _pipecat_readiness(
    required: ConformanceCaseResult | None,
    speed: ConformanceCaseResult | None,
    instructions: ConformanceCaseResult | None,
) -> IntegrationReadiness:
    cases = ["required fields with response_format", "speed field", "instructions field"]
    if _audio_success(required) and _success(speed) and _success(instructions):
        return IntegrationReadiness(
            status="likely_ready",
            reason="OpenAI-style speech request, speed, and instructions fields passed basic checks",
            cases=cases,
        )
    checks = [
        ("basic speech request did not return audio", required, _audio_success),
        ("speed field failed", speed, _success),
        ("instructions field failed", instructions, _success),
    ]
    failures = [_case_failure(case, name) for name, case, passed in checks if not passed(case)]
    return IntegrationReadiness(
        status="failed",
        reason="; ".join(failures),
        cases=cases,
    )


def _case(report: ConformanceReport, name: str) -> ConformanceCaseResult | None:
    return next((case for case in report.cases if case.name == name), None)


def _success(case: ConformanceCaseResult | None) -> bool:
    return case is not None and case.passed


def _audio_success(case: ConformanceCaseResult | None) -> bool:
    if case is None or not case.passed or case.status_code != 200:
        return False
    if case.response_kind == "audio":
        return True
    content_type = case.content_type or ""
    return content_type.startswith("audio/") or "application/octet-stream" in content_type


def _case_failure(case: ConformanceCaseResult | None, fallback: str) -> str:
    if case is None:
        return f"{fallback}: case not present"
    if case.failure:
        return case.failure
    return fallback
