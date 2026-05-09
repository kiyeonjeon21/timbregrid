from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from timbregrid.benchmark_suites import get_benchmark_suite
from timbregrid.manifest import ManifestError, load_manifest
from timbregrid.models import BenchmarkResult, BenchmarkRun


class BenchmarkStoreError(ValueError):
    """Raised when benchmark artifacts cannot be loaded."""


PROFILE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
REQUIRED_HARDWARE_KEYS = ("os", "machine", "processor", "profile", "python")
OK_RUN_FIELDS = (
    "total_generation_ms",
    "time_to_first_audio_ms",
    "real_time_factor",
    "memory_peak_bytes",
    "output_duration_ms",
    "sample_rate_hz",
    "format",
)
AGGREGATE_AVERAGE_METRICS = (
    "time_to_first_audio_ms",
    "total_generation_ms",
    "real_time_factor",
    "output_duration_ms",
)


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


def validate_benchmark_result(
    path: Path,
    *,
    manifest_dir: Path | None = Path("manifests"),
) -> BenchmarkResult:
    result = load_benchmark_result(path)
    try:
        suite = get_benchmark_suite(result.suite)
    except ValueError as exc:
        raise BenchmarkStoreError(str(exc)) from exc

    _validate_model_id(result.model, manifest_dir)
    _validate_hardware(result)
    _validate_suite_prompts(result, suite.prompts)
    _validate_run_entries(result)
    _validate_metrics(result)
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


def _validate_model_id(model: str, manifest_dir: Path | None) -> None:
    if manifest_dir is None or not manifest_dir.exists():
        return

    manifest_ids: set[str] = set()
    for path in sorted(manifest_dir.glob("*.yaml")):
        try:
            manifest_ids.add(load_manifest(path).id)
        except ManifestError as exc:
            raise BenchmarkStoreError(f"Invalid manifest while validating benchmarks: {path}: {exc}") from exc

    if manifest_ids and model not in manifest_ids:
        raise BenchmarkStoreError(
            f"Unknown benchmark model id: {model}. Add a matching manifest under {manifest_dir}."
        )


def _validate_hardware(result: BenchmarkResult) -> None:
    for key in REQUIRED_HARDWARE_KEYS:
        if key not in result.hardware:
            raise BenchmarkStoreError(f"Invalid benchmark hardware: missing hardware.{key}")
        if key != "processor" and not str(result.hardware[key]).strip():
            raise BenchmarkStoreError(f"Invalid benchmark hardware: hardware.{key} must not be empty")

    profile = result.hardware["profile"]
    if not isinstance(profile, str) or not PROFILE_PATTERN.fullmatch(profile):
        raise BenchmarkStoreError(
            "Invalid benchmark hardware: hardware.profile must use lowercase letters, "
            "numbers, dots, underscores, or hyphens"
        )


def _validate_suite_prompts(result: BenchmarkResult, expected_prompts: tuple[str, ...]) -> None:
    prompts = tuple(run.prompt for run in result.runs)
    if prompts != expected_prompts:
        raise BenchmarkStoreError(
            f"Invalid benchmark prompts: runs must match suite {result.suite!r}"
        )


def _validate_run_entries(result: BenchmarkResult) -> None:
    for index, run in enumerate(result.runs):
        label = f"runs[{index}]"
        if run.ok:
            missing = [field for field in OK_RUN_FIELDS if getattr(run, field) is None]
            if missing:
                raise BenchmarkStoreError(
                    f"Invalid benchmark run: {label} is ok but missing {', '.join(missing)}"
                )
            if run.error is not None:
                raise BenchmarkStoreError(f"Invalid benchmark run: {label} is ok but has error")
            _validate_non_negative(run, label, "total_generation_ms")
            _validate_non_negative(run, label, "time_to_first_audio_ms")
            _validate_non_negative(run, label, "real_time_factor")
            _validate_non_negative(run, label, "memory_peak_bytes")
            _validate_positive(run, label, "output_duration_ms")
            _validate_positive(run, label, "sample_rate_hz")
        elif not run.error:
            raise BenchmarkStoreError(f"Invalid benchmark run: {label} failed but has no error")


def _validate_non_negative(run: BenchmarkRun, label: str, field: str) -> None:
    value = getattr(run, field)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise BenchmarkStoreError(f"Invalid benchmark run: {label}.{field} must be >= 0")


def _validate_positive(run: BenchmarkRun, label: str, field: str) -> None:
    value = getattr(run, field)
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise BenchmarkStoreError(f"Invalid benchmark run: {label}.{field} must be > 0")


def _validate_metrics(result: BenchmarkResult) -> None:
    runs = _integer_metric(result, "runs")
    failures = _integer_metric(result, "failures")
    actual_failures = len([run for run in result.runs if not run.ok])
    if runs != len(result.runs):
        raise BenchmarkStoreError(
            f"Invalid benchmark metrics: runs={runs} does not match {len(result.runs)} run entries"
        )
    if failures != actual_failures:
        raise BenchmarkStoreError(
            f"Invalid benchmark metrics: failures={failures} does not match {actual_failures} failed runs"
        )

    expected_failure_rate = failures / runs if runs else 0.0
    _assert_metric_close(result, "failure_rate", expected_failure_rate)

    for metric in AGGREGATE_AVERAGE_METRICS:
        _assert_metric_close(result, metric, _average_ok_run_metric(result.runs, metric))

    expected_peak = max((run.memory_peak_bytes or 0 for run in result.runs), default=0)
    if _integer_metric(result, "memory_peak_bytes") != expected_peak:
        raise BenchmarkStoreError(
            "Invalid benchmark metrics: memory_peak_bytes does not match run entries"
        )


def _integer_metric(result: BenchmarkResult, name: str) -> int:
    value = _numeric_metric(result, name)
    if not float(value).is_integer():
        raise BenchmarkStoreError(f"Invalid benchmark metrics: {name} must be an integer")
    return int(value)


def _numeric_metric(result: BenchmarkResult, name: str) -> float:
    if name not in result.metrics:
        raise BenchmarkStoreError(f"Invalid benchmark metrics: missing {name}")
    value = result.metrics[name]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise BenchmarkStoreError(f"Invalid benchmark metrics: {name} must be numeric")
    value = float(value)
    if not math.isfinite(value):
        raise BenchmarkStoreError(f"Invalid benchmark metrics: {name} must be finite")
    return value


def _assert_metric_close(result: BenchmarkResult, name: str, expected: float) -> None:
    actual = _numeric_metric(result, name)
    if not math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6):
        raise BenchmarkStoreError(
            f"Invalid benchmark metrics: {name}={actual:g} does not match expected {expected:g}"
        )


def _average_ok_run_metric(runs: list[BenchmarkRun], name: str) -> float:
    values = [float(getattr(run, name)) for run in runs if run.ok and getattr(run, name) is not None]
    return float(sum(values) / len(values)) if values else 0.0
