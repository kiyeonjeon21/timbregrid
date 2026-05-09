from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from timbregrid.benchmark_suites import get_benchmark_suite
from timbregrid.models import BenchmarkResult


class BenchmarkStoreError(ValueError):
    """Raised when benchmark artifacts cannot be loaded."""


@dataclass(frozen=True)
class BenchmarkSummary:
    model: str
    suite: str
    hardware_profile: str | None
    time_to_first_audio_ms: float
    total_generation_ms: float
    real_time_factor: float
    failure_rate: float
    hardware: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_benchmark_results(benchmark_dir: Path | None) -> list[BenchmarkResult]:
    if benchmark_dir is None or not benchmark_dir.exists():
        return []
    if not benchmark_dir.is_dir():
        raise BenchmarkStoreError(f"Benchmark path is not a directory: {benchmark_dir}")

    results: list[BenchmarkResult] = []
    for path in sorted(benchmark_dir.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BenchmarkStoreError(f"Invalid benchmark JSON: {path}") from exc

        try:
            results.append(BenchmarkResult.model_validate(raw))
        except ValidationError as exc:
            raise BenchmarkStoreError(f"Invalid benchmark schema: {path}: {exc}") from exc

    return results


def load_benchmark_result(path: Path) -> BenchmarkResult:
    if not path.exists():
        raise BenchmarkStoreError(f"Benchmark file does not exist: {path}")
    if not path.is_file():
        raise BenchmarkStoreError(f"Benchmark path is not a file: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BenchmarkStoreError(f"Invalid benchmark JSON: {path}") from exc

    try:
        return BenchmarkResult.model_validate(raw)
    except ValidationError as exc:
        raise BenchmarkStoreError(f"Invalid benchmark schema: {path}: {exc}") from exc


def validate_benchmark_result(path: Path) -> BenchmarkResult:
    result = load_benchmark_result(path)
    try:
        get_benchmark_suite(result.suite)
    except ValueError as exc:
        raise BenchmarkStoreError(str(exc)) from exc

    runs = int(result.metrics.get("runs", -1))
    failures = int(result.metrics.get("failures", -1))
    actual_failures = len([run for run in result.runs if not run.ok])
    if runs != len(result.runs):
        raise BenchmarkStoreError(
            f"Invalid benchmark metrics: runs={runs} does not match {len(result.runs)} run entries"
        )
    if failures != actual_failures:
        raise BenchmarkStoreError(
            f"Invalid benchmark metrics: failures={failures} does not match {actual_failures} failed runs"
        )
    return result


def best_benchmark(
    results: list[BenchmarkResult],
    *,
    model: str,
    suite: str,
    hardware_profile: str | None = None,
) -> BenchmarkSummary | None:
    matches = [
        result
        for result in results
        if result.model == model
        and result.suite == suite
        and _matches_hardware_profile(result, hardware_profile)
    ]
    if not matches:
        return None

    selected = sorted(matches, key=_result_sort_key)[0]
    return _summary(selected)


def _matches_hardware_profile(result: BenchmarkResult, hardware_profile: str | None) -> bool:
    if hardware_profile is None:
        return True
    return result.hardware.get("profile") == hardware_profile


def _result_sort_key(result: BenchmarkResult) -> tuple[float, float, float, str]:
    return (
        float(result.metrics.get("failure_rate", 1.0)),
        float(result.metrics.get("time_to_first_audio_ms", float("inf"))),
        float(result.metrics.get("real_time_factor", float("inf"))),
        result.created_at,
    )


def _summary(result: BenchmarkResult) -> BenchmarkSummary:
    return BenchmarkSummary(
        model=result.model,
        suite=result.suite,
        hardware_profile=_profile(result),
        time_to_first_audio_ms=float(result.metrics.get("time_to_first_audio_ms", 0.0)),
        total_generation_ms=float(result.metrics.get("total_generation_ms", 0.0)),
        real_time_factor=float(result.metrics.get("real_time_factor", 0.0)),
        failure_rate=float(result.metrics.get("failure_rate", 0.0)),
        hardware=result.hardware,
    )


def _profile(result: BenchmarkResult) -> str | None:
    profile = result.hardware.get("profile")
    return str(profile) if profile is not None else None
