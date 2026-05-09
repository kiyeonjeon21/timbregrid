import json
from pathlib import Path

from typer.testing import CliRunner

from timbregrid.cli import app, resolve_serve_config
from timbregrid.conformance import ConformanceCaseResult, ConformanceReport
from timbregrid.doctor import build_doctor_report


def test_manifest_validate_cli() -> None:
    result = CliRunner().invoke(app, ["manifest", "validate", "manifests/fake-tts.yaml"])

    assert result.exit_code == 0
    assert "OK" in result.stdout
    assert "fake:tts" in result.stdout


def test_bench_cli_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "bench.json"

    result = CliRunner().invoke(
        app,
        [
            "bench",
            "fake:tts",
            "--suite",
            "realtime-agent",
            "--hardware-profile",
            "generic-ci",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["model"] == "fake:tts"
    assert body["suite"] == "realtime-agent"
    assert body["hardware"]["profile"] == "generic-ci"
    assert body["metrics"]["runs"] == 3
    assert body["metrics"]["failures"] == 0


def test_bench_cli_accepts_narration_suite(tmp_path: Path) -> None:
    output = tmp_path / "bench.json"

    result = CliRunner().invoke(
        app,
        ["bench", "fake:tts", "--suite", "narration", "--output", str(output)],
    )

    assert result.exit_code == 0
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["model"] == "fake:tts"
    assert body["suite"] == "narration"
    assert body["metrics"]["runs"] >= 3
    assert body["metrics"]["failures"] == 0


def test_bench_cli_lists_available_suites_for_unknown_suite(tmp_path: Path) -> None:
    output = tmp_path / "bench.json"

    result = CliRunner().invoke(
        app,
        ["bench", "fake:tts", "--suite", "missing-suite", "--output", str(output)],
    )

    assert result.exit_code == 1
    assert "Unknown benchmark suite: missing-suite" in result.stderr
    assert "realtime-agent" in result.stderr
    assert "narration" in result.stderr


def test_bench_validate_cli_accepts_example() -> None:
    result = CliRunner().invoke(
        app,
        ["bench", "validate", "benchmarks/examples/fake-tts.realtime-agent.json"],
    )

    assert result.exit_code == 0
    assert "OK benchmarks/examples/fake-tts.realtime-agent.json" in result.stdout
    assert "fake:tts" in result.stdout


def test_bench_validate_cli_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{", encoding="utf-8")

    result = CliRunner().invoke(app, ["bench", "validate", str(path)])

    assert result.exit_code == 1
    assert "Invalid benchmark JSON" in result.stderr


def test_models_list_cli_includes_known_models() -> None:
    result = CliRunner().invoke(app, ["models", "list"])

    assert result.exit_code == 0
    assert "fake:tts" in result.stdout
    assert "kokoro:82m" in result.stdout
    assert "kitten-tts:nano-0.8" in result.stdout
    assert "chatterbox:tts" in result.stdout
    assert "qwen3-tts:0.6b-base" in result.stdout


def test_models_inspect_cli_writes_json() -> None:
    result = CliRunner().invoke(app, ["models", "inspect", "kokoro:82m"])

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["id"] == "kokoro:82m"
    assert body["executable"] is True
    assert body["requires_extra"] == "kokoro"


def test_models_inspect_cli_writes_manifest_only_json() -> None:
    result = CliRunner().invoke(app, ["models", "inspect", "chatterbox:tts"])

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["id"] == "chatterbox:tts"
    assert body["executable"] is False
    assert body["status"] == "manifest-only"


def test_registry_build_cli_writes_artifacts(tmp_path: Path) -> None:
    index = tmp_path / "registry" / "index.json"
    matrix = tmp_path / "docs" / "support-matrix.md"

    result = CliRunner().invoke(
        app,
        [
            "registry",
            "build",
            "--index",
            str(index),
            "--matrix",
            str(matrix),
        ],
    )

    assert result.exit_code == 0
    body = json.loads(index.read_text(encoding="utf-8"))
    assert body["model_count"] == 5
    assert "`fake:tts`" in matrix.read_text(encoding="utf-8")


def test_registry_build_check_cli_detects_stale_artifacts(tmp_path: Path) -> None:
    index = tmp_path / "registry" / "index.json"
    matrix = tmp_path / "docs" / "support-matrix.md"

    result = CliRunner().invoke(
        app,
        ["registry", "build", "--index", str(index), "--matrix", str(matrix)],
    )
    assert result.exit_code == 0

    result = CliRunner().invoke(
        app,
        ["registry", "build", "--check", "--index", str(index), "--matrix", str(matrix)],
    )
    assert result.exit_code == 0
    assert "OK registry artifacts are current" in result.stdout

    matrix.write_text("stale\n", encoding="utf-8")
    result = CliRunner().invoke(
        app,
        ["registry", "build", "--check", "--index", str(index), "--matrix", str(matrix)],
    )
    assert result.exit_code == 1
    assert "Registry artifacts are stale" in result.stderr


def test_registry_audit_cli_can_skip_network() -> None:
    result = CliRunner().invoke(app, ["registry", "audit", "--skip-network"])

    assert result.exit_code == 0
    assert "OK registry audit passed" in result.stdout
    assert "network skipped" in result.stdout


def test_route_explain_cli_writes_json(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.registry.importlib.util.find_spec", lambda _: None)

    result = CliRunner().invoke(
        app,
        [
            "route",
            "explain",
            "--model",
            "auto",
            "--voice",
            "alloy",
            "--response-format",
            "wav",
            "--purpose",
            "realtime",
            "--license-policy",
            "commercial_ok",
            "--target-latency-ms",
            "350",
            "--hardware-profile",
            "generic-ci",
        ],
    )

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["selected_model"] == "fake:tts"
    assert body["applied_hints"]["purpose"] == "realtime"
    assert body["applied_hints"]["hardware_profile"] == "generic-ci"
    assert body["benchmark_data"] == "used"
    assert body["selected_benchmark"]["hardware_profile"] == "generic-ci"


def test_route_explain_cli_preserves_requested_benchmark_suite(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.registry.importlib.util.find_spec", lambda _: None)

    result = CliRunner().invoke(
        app,
        [
            "route",
            "explain",
            "--model",
            "auto",
            "--voice",
            "alloy",
            "--response-format",
            "wav",
            "--purpose",
            "realtime",
            "--suite",
            "narration",
        ],
    )

    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body["selected_model"] == "fake:tts"
    assert body["applied_hints"]["benchmark_suite"] == "narration"
    assert body["benchmark_data"] == "missing"


def test_route_explain_cli_returns_no_route(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.registry.importlib.util.find_spec", lambda _: None)

    result = CliRunner().invoke(
        app,
        [
            "route",
            "explain",
            "--model",
            "auto",
            "--voice",
            "alloy",
            "--response-format",
            "wav",
            "--purpose",
            "cloning",
        ],
    )

    assert result.exit_code == 1
    assert "No route found" in result.stderr


def test_resolve_serve_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("TIMBREGRID_MODEL", raising=False)
    monkeypatch.delenv("TIMBREGRID_HOST", raising=False)
    monkeypatch.delenv("TIMBREGRID_PORT", raising=False)
    monkeypatch.delenv("TIMBREGRID_BENCHMARK_DIR", raising=False)
    monkeypatch.delenv("TIMBREGRID_VOICE_CATALOG", raising=False)

    assert resolve_serve_config() == (
        "fake:tts",
        "127.0.0.1",
        8889,
        Path("benchmarks/examples"),
        None,
    )


def test_resolve_serve_config_uses_env(monkeypatch) -> None:
    monkeypatch.setenv("TIMBREGRID_MODEL", "kokoro:82m")
    monkeypatch.setenv("TIMBREGRID_HOST", "0.0.0.0")
    monkeypatch.setenv("TIMBREGRID_PORT", "9999")
    monkeypatch.setenv("TIMBREGRID_BENCHMARK_DIR", "benchmarks/custom")
    monkeypatch.setenv("TIMBREGRID_VOICE_CATALOG", "voices/custom.json")

    assert resolve_serve_config() == (
        "kokoro:82m",
        "0.0.0.0",
        9999,
        Path("benchmarks/custom"),
        Path("voices/custom.json"),
    )


def test_resolve_serve_config_prefers_arguments(monkeypatch) -> None:
    monkeypatch.setenv("TIMBREGRID_MODEL", "kokoro:82m")
    monkeypatch.setenv("TIMBREGRID_HOST", "0.0.0.0")
    monkeypatch.setenv("TIMBREGRID_PORT", "9999")
    monkeypatch.setenv("TIMBREGRID_BENCHMARK_DIR", "benchmarks/custom")
    monkeypatch.setenv("TIMBREGRID_VOICE_CATALOG", "voices/custom.json")

    assert resolve_serve_config(
        "fake:tts",
        "127.0.0.1",
        7777,
        Path("benchmarks/args"),
        Path("voices/args.json"),
    ) == (
        "fake:tts",
        "127.0.0.1",
        7777,
        Path("benchmarks/args"),
        Path("voices/args.json"),
    )


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


def test_doctor_cli_writes_json_report(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "doctor.json"

    monkeypatch.setattr("timbregrid.cli.run_doctor", lambda *_, **__: _doctor_report(failed=False))
    result = CliRunner().invoke(
        app,
        [
            "doctor",
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
    assert "OK doctor: 3/3 conformance cases passed" in result.stdout
    assert "open_webui_tts: ready" in result.stdout
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["schema_version"] == "0.1"
    assert body["integration_readiness"]["open_webui_tts"]["status"] == "ready"


def test_doctor_cli_returns_failure_exit_code(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.cli.run_doctor", lambda *_, **__: _doctor_report(failed=True))
    result = CliRunner().invoke(app, ["doctor", "http://example.test/v1"])

    assert result.exit_code == 1
    assert "FAIL doctor: 2/3 conformance cases passed" in result.stderr
    assert "FAIL required fields with response_format: expected HTTP 200" in result.stderr


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


def _doctor_report(*, failed: bool):
    required = ConformanceCaseResult(
        name="required fields with response_format",
        passed=not failed,
        expectation="success",
        request_payload={"model": "fake:tts", "input": "hello", "voice": "alloy"},
        status_code=500 if failed else 200,
        content_type="application/json" if failed else "audio/wav",
        content_length=0 if failed else 10,
        elapsed_ms=1.0,
        response_kind="json" if failed else "audio",
        failure="expected HTTP 200, got 500" if failed else None,
    )
    cases = [
        required,
        _doctor_case("speed field"),
        _doctor_case("instructions field"),
    ]
    passed = sum(1 for case in cases if case.passed)
    failed_count = len(cases) - passed
    return build_doctor_report(
        ConformanceReport(
            schema_version="0.1",
            created_at="2026-05-09T00:00:00+00:00",
            base_url="http://example.test/v1",
            endpoint="audio.speech",
            config={"model": "fake:tts", "voice": "alloy", "response_format": "wav", "timeout": 10},
            summary={
                "total": len(cases),
                "passed": passed,
                "failed": failed_count,
                "failure_rate": failed_count / len(cases),
            },
            cases=cases,
        )
    )


def _doctor_case(name: str) -> ConformanceCaseResult:
    return ConformanceCaseResult(
        name=name,
        passed=True,
        expectation="success",
        request_payload={"model": "fake:tts", "input": "hello", "voice": "alloy"},
        status_code=200,
        content_type="audio/wav",
        content_length=10,
        elapsed_ms=1.0,
        response_kind="audio",
    )
