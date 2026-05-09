import json
from pathlib import Path

from typer.testing import CliRunner

from timbregrid.cli import app
from timbregrid.conformance import ConformanceCaseResult, ConformanceReport


def test_manifest_validate_cli() -> None:
    result = CliRunner().invoke(app, ["manifest", "validate", "manifests/fake-tts.yaml"])

    assert result.exit_code == 0
    assert "OK" in result.stdout
    assert "fake:tts" in result.stdout


def test_bench_cli_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "bench.json"

    result = CliRunner().invoke(
        app,
        ["bench", "fake:tts", "--suite", "realtime-agent", "--output", str(output)],
    )

    assert result.exit_code == 0
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["model"] == "fake:tts"
    assert body["suite"] == "realtime-agent"
    assert body["metrics"]["runs"] == 3
    assert body["metrics"]["failures"] == 0


def test_conformance_cli_writes_json_report(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "conformance.json"

    monkeypatch.setattr("timbregrid.cli.run_conformance", lambda *_, **__: _report(failed=0))
    result = CliRunner().invoke(
        app,
        [
            "conformance",
            "http://example.test/v1",
            "--model",
            "fake:tts",
            "--voice",
            "alloy",
            "--response-format",
            "wav",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert "OK 1/1 conformance cases passed" in result.stdout
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["schema_version"] == "0.1"
    assert body["summary"]["passed"] == 1


def test_conformance_cli_returns_failure_exit_code(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.cli.run_conformance", lambda *_, **__: _report(failed=1))
    result = CliRunner().invoke(app, ["conformance", "http://example.test/v1"])

    assert result.exit_code == 1
    assert "FAIL broken: expected HTTP 200" in result.stderr


def _report(*, failed: int) -> ConformanceReport:
    case = ConformanceCaseResult(
        name="broken" if failed else "ok",
        passed=failed == 0,
        expectation="success",
        request_payload={"model": "fake:tts", "input": "hello", "voice": "alloy"},
        status_code=500 if failed else 200,
        content_type="application/json" if failed else "application/octet-stream",
        content_length=0 if failed else 10,
        elapsed_ms=1.0,
        failure="expected HTTP 200" if failed else None,
    )
    return ConformanceReport(
        schema_version="0.1",
        created_at="2026-05-09T00:00:00+00:00",
        base_url="http://example.test/v1",
        endpoint="audio.speech",
        config={"model": "fake:tts", "voice": "alloy", "response_format": "wav", "timeout": 10},
        summary={"total": 1, "passed": 0 if failed else 1, "failed": failed, "failure_rate": failed},
        cases=[case],
    )
