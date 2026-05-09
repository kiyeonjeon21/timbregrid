from pathlib import Path

from timbregrid.conformance import ConformanceCaseResult, ConformanceReport
from timbregrid.doctor import build_doctor_report, write_doctor_report


def test_doctor_report_marks_integrations_ready_for_audio_success() -> None:
    report = build_doctor_report(_conformance_report())

    assert report.ok
    assert report.integration_readiness["open_webui_tts"].status == "ready"
    assert report.integration_readiness["pipecat_openai_tts"].status == "likely_ready"


def test_doctor_report_marks_integrations_failed_when_speech_request_fails() -> None:
    report = build_doctor_report(
        _conformance_report(
            required=_case(
                "required fields with response_format",
                passed=False,
                status_code=500,
                content_type="application/json",
                response_kind="json",
                failure="expected HTTP 200, got 500",
            )
        )
    )

    assert not report.ok
    assert report.integration_readiness["open_webui_tts"].status == "failed"
    assert report.integration_readiness["pipecat_openai_tts"].status == "failed"
    assert "expected HTTP 200" in report.integration_readiness["open_webui_tts"].reason


def test_write_doctor_report_preserves_conformance_failures(tmp_path: Path) -> None:
    output = tmp_path / "doctor.json"
    report = build_doctor_report(
        _conformance_report(
            required=_case(
                "required fields with response_format",
                passed=False,
                status_code=500,
                content_type="application/json",
                response_kind="json",
                failure="expected HTTP 200, got 500",
            )
        )
    )

    write_doctor_report(report, output)

    body = output.read_text(encoding="utf-8")
    assert '"open_webui_tts"' in body
    assert '"expected HTTP 200, got 500"' in body


def _conformance_report(
    *,
    required: ConformanceCaseResult | None = None,
) -> ConformanceReport:
    cases = [
        required or _case("required fields with response_format"),
        _case("speed field"),
        _case("instructions field"),
    ]
    passed = sum(1 for case in cases if case.passed)
    failed = len(cases) - passed
    return ConformanceReport(
        schema_version="0.1",
        created_at="2026-05-09T00:00:00+00:00",
        base_url="http://example.test/v1",
        endpoint="audio.speech",
        config={"model": "fake:tts", "voice": "alloy", "response_format": "wav", "timeout": 10},
        summary={"total": len(cases), "passed": passed, "failed": failed, "failure_rate": failed / len(cases)},
        cases=cases,
    )


def _case(
    name: str,
    *,
    passed: bool = True,
    status_code: int = 200,
    content_type: str = "audio/wav",
    response_kind: str = "audio",
    failure: str | None = None,
) -> ConformanceCaseResult:
    return ConformanceCaseResult(
        name=name,
        passed=passed,
        expectation="success",
        request_payload={"model": "fake:tts", "input": "hello", "voice": "alloy"},
        status_code=status_code,
        content_type=content_type,
        content_length=10 if passed else 0,
        elapsed_ms=1.0,
        response_kind=response_kind,
        failure=failure,
    )
