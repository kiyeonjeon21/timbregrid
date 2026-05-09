import json
from pathlib import Path

import pytest

from timbregrid.benchmark_store import (
    BenchmarkStoreError,
    best_benchmark,
    load_benchmark_results,
    validate_benchmark_result,
)


EXAMPLE_BENCHMARK = Path("benchmarks/examples/fake-tts.realtime-agent.json")


def test_load_example_benchmark_results() -> None:
    results = load_benchmark_results(Path("benchmarks/examples"))

    assert len(results) == 1
    assert results[0].model == "fake:tts"
    assert results[0].suite == "realtime-agent"


def test_best_benchmark_matches_hardware_profile() -> None:
    results = load_benchmark_results(Path("benchmarks/examples"))

    benchmark = best_benchmark(
        results,
        model="fake:tts",
        suite="realtime-agent",
        hardware_profile="generic-ci",
    )

    assert benchmark is not None
    assert benchmark.hardware_profile == "generic-ci"
    assert benchmark.time_to_first_audio_ms == 0.0


def test_best_benchmark_returns_none_for_profile_miss() -> None:
    results = load_benchmark_results(Path("benchmarks/examples"))

    benchmark = best_benchmark(
        results,
        model="fake:tts",
        suite="realtime-agent",
        hardware_profile="missing-profile",
    )

    assert benchmark is None


def test_validate_benchmark_result_accepts_example() -> None:
    result = validate_benchmark_result(EXAMPLE_BENCHMARK)

    assert result.model == "fake:tts"
    assert result.suite == "realtime-agent"


def test_load_benchmark_results_rejects_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="Invalid benchmark JSON"):
        load_benchmark_results(tmp_path)


def test_load_benchmark_results_rejects_invalid_schema(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{}", encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="Invalid benchmark schema"):
        load_benchmark_results(tmp_path)


def test_validate_benchmark_result_rejects_metric_mismatch(tmp_path: Path) -> None:
    body = _example_body()
    body["metrics"]["runs"] = 99
    path = tmp_path / "bad-metrics.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="runs=99"):
        validate_benchmark_result(path)


def test_validate_benchmark_result_rejects_unknown_model(tmp_path: Path) -> None:
    body = _example_body()
    body["model"] = "missing:model"
    path = tmp_path / "unknown-model.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="Unknown benchmark model id"):
        validate_benchmark_result(path)


def test_validate_benchmark_result_rejects_missing_hardware_profile(tmp_path: Path) -> None:
    body = _example_body()
    body["hardware"].pop("profile")
    path = tmp_path / "missing-profile.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="missing hardware.profile"):
        validate_benchmark_result(path)


def test_validate_benchmark_result_rejects_suite_prompt_mismatch(tmp_path: Path) -> None:
    body = _example_body()
    body["runs"][0]["prompt"] = "not part of the realtime-agent suite"
    path = tmp_path / "bad-prompts.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="runs must match suite"):
        validate_benchmark_result(path)


def test_validate_benchmark_result_rejects_average_metric_mismatch(tmp_path: Path) -> None:
    body = _example_body()
    body["metrics"]["total_generation_ms"] = 999
    path = tmp_path / "bad-average.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="total_generation_ms"):
        validate_benchmark_result(path)


def test_validate_benchmark_result_rejects_incomplete_successful_run(tmp_path: Path) -> None:
    body = _example_body()
    body["runs"][0]["time_to_first_audio_ms"] = None
    path = tmp_path / "bad-run.json"
    path.write_text(json.dumps(body), encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="missing time_to_first_audio_ms"):
        validate_benchmark_result(path)


def _example_body() -> dict:
    return json.loads(EXAMPLE_BENCHMARK.read_text(encoding="utf-8"))
