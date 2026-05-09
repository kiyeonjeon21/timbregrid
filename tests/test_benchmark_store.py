from pathlib import Path

import pytest

from timbregrid.benchmark_store import BenchmarkStoreError, best_benchmark, load_benchmark_results


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


def test_load_benchmark_results_rejects_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="Invalid benchmark JSON"):
        load_benchmark_results(tmp_path)


def test_load_benchmark_results_rejects_invalid_schema(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{}", encoding="utf-8")

    with pytest.raises(BenchmarkStoreError, match="Invalid benchmark schema"):
        load_benchmark_results(tmp_path)
