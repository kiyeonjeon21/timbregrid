from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from timbregrid.benchmark_store import (
    BenchmarkSummary,
    best_benchmark,
    load_benchmark_results,
)
from timbregrid.manifest import ManifestError, load_manifest
from timbregrid.models import LicensePolicy, ModelManifest, RoutingPurpose, SpeechRequest
from timbregrid.registry import ModelEntry, list_models


PERMISSIVE_LICENSES = {
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
    "mit",
}


class RouteNotFound(ValueError):
    def __init__(self, message: str, skipped_candidates: list[SkippedCandidate]) -> None:
        super().__init__(message)
        self.skipped_candidates = skipped_candidates


@dataclass(frozen=True)
class SkippedCandidate:
    model: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class RouteDecision:
    requested_model: str
    selected_model: str
    reason: str
    applied_hints: dict[str, Any]
    benchmark_data: str
    selected_benchmark: BenchmarkSummary | None
    skipped_candidates: list[SkippedCandidate]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_model": self.requested_model,
            "selected_model": self.selected_model,
            "reason": self.reason,
            "applied_hints": self.applied_hints,
            "benchmark_data": self.benchmark_data,
            "selected_benchmark": (
                self.selected_benchmark.to_dict() if self.selected_benchmark is not None else None
            ),
            "skipped_candidates": [candidate.to_dict() for candidate in self.skipped_candidates],
        }


@dataclass(frozen=True)
class _Candidate:
    entry: ModelEntry
    manifest: ModelManifest


def resolve_route(
    request: SpeechRequest,
    *,
    default_model: str = "fake:tts",
    benchmark_dir: Path | None = None,
    suite: str = "realtime-agent",
) -> RouteDecision:
    if request.model != "auto":
        return RouteDecision(
            requested_model=request.model,
            selected_model=request.model,
            reason="explicit model requested",
            applied_hints=_applied_hints(request, suite),
            benchmark_data="not_used",
            selected_benchmark=None,
            skipped_candidates=[],
        )

    candidates, skipped = _available_candidates()
    matches: list[_Candidate] = []

    for candidate in candidates:
        skip_reason = _skip_reason(candidate, request)
        if skip_reason is not None:
            skipped.append(SkippedCandidate(candidate.entry.id, skip_reason))
            continue
        matches.append(candidate)

    if not matches:
        raise RouteNotFound("No route found for model='auto' with the requested hints", skipped)

    benchmarks = _candidate_benchmarks(matches, request, benchmark_dir, suite)
    selected = sorted(
        matches,
        key=lambda candidate: _candidate_sort_key(candidate, request, default_model, benchmarks),
    )[0]
    selected_benchmark = benchmarks.get(selected.entry.id)
    benchmark_data = _benchmark_data_status(benchmark_dir, benchmarks, selected_benchmark)
    return RouteDecision(
        requested_model=request.model,
        selected_model=selected.entry.id,
        reason=_selection_reason(
            selected,
            request,
            len(matches),
            benchmark_data=benchmark_data,
            benchmark=selected_benchmark,
        ),
        applied_hints=_applied_hints(request, suite),
        benchmark_data=benchmark_data,
        selected_benchmark=selected_benchmark,
        skipped_candidates=skipped,
    )


def _available_candidates() -> tuple[list[_Candidate], list[SkippedCandidate]]:
    candidates: list[_Candidate] = []
    skipped: list[SkippedCandidate] = []

    for entry in sorted(list_models(), key=lambda item: item.id):
        if not entry.executable:
            skipped.append(SkippedCandidate(entry.id, "model is manifest-only"))
            continue
        if not entry.available:
            skipped.append(SkippedCandidate(entry.id, entry.status))
            continue
        if entry.manifest_path is None:
            skipped.append(SkippedCandidate(entry.id, "model has no manifest"))
            continue
        try:
            manifest = load_manifest(Path(entry.manifest_path))
        except ManifestError as exc:
            skipped.append(SkippedCandidate(entry.id, f"invalid manifest: {exc}"))
            continue
        candidates.append(_Candidate(entry=entry, manifest=manifest))

    return candidates, skipped


def _skip_reason(candidate: _Candidate, request: SpeechRequest) -> str | None:
    if request.response_format not in candidate.manifest.audio.formats:
        return f"does not support response_format={request.response_format}"
    if not _matches_purpose(candidate.manifest, request.purpose):
        return f"does not match purpose={request.purpose}"
    if not _matches_license(candidate.manifest, request.license_policy):
        return f"does not match license_policy={request.license_policy}"
    return None


def _candidate_sort_key(
    candidate: _Candidate,
    request: SpeechRequest,
    default_model: str,
    benchmarks: dict[str, BenchmarkSummary],
) -> tuple[float, float, float, float, float, int, int, str]:
    benchmark = benchmarks.get(candidate.entry.id)
    benchmark_priority = 0.0
    latency_miss = 0.0
    failure_rate = 0.0
    time_to_first_audio_ms = 0.0
    real_time_factor = 0.0
    if request.target_latency_ms is not None and benchmarks:
        if benchmark is None:
            benchmark_priority = 1.0
            latency_miss = 1.0
            failure_rate = float("inf")
            time_to_first_audio_ms = float("inf")
            real_time_factor = float("inf")
        else:
            latency_miss = (
                0.0 if benchmark.time_to_first_audio_ms <= request.target_latency_ms else 1.0
            )
            failure_rate = benchmark.failure_rate
            time_to_first_audio_ms = benchmark.time_to_first_audio_ms
            real_time_factor = benchmark.real_time_factor

    real_adapter_score = 1 if candidate.entry.id != "fake:tts" else 0
    purpose_score = _purpose_score(candidate.manifest, request.purpose)
    default_score = 1 if candidate.entry.id == default_model else 0
    return (
        benchmark_priority,
        latency_miss,
        failure_rate,
        time_to_first_audio_ms,
        real_time_factor,
        -real_adapter_score,
        -(purpose_score + default_score),
        candidate.entry.id,
    )


def _purpose_score(manifest: ModelManifest, purpose: RoutingPurpose | None) -> int:
    if purpose == "multilingual" and manifest.capabilities.multilingual == "full":
        return 3
    if purpose == "multilingual" and manifest.capabilities.multilingual == "limited":
        return 2
    if purpose in {"narration", "dialogue"} and manifest.capabilities.long_form == "full":
        return 3
    if purpose in {"narration", "dialogue"} and manifest.capabilities.long_form == "limited":
        return 2
    if purpose == "edge" and manifest.runtime.acceleration.cpu:
        return 2
    if purpose == "realtime":
        return 1
    return 0


def _matches_purpose(manifest: ModelManifest, purpose: RoutingPurpose | None) -> bool:
    if purpose is None or purpose == "realtime":
        return True
    if purpose == "cloning":
        return manifest.capabilities.voice_cloning
    if purpose == "multilingual":
        return manifest.capabilities.multilingual != "none"
    if purpose in {"narration", "dialogue"}:
        return manifest.capabilities.long_form != "none"
    if purpose == "edge":
        return manifest.runtime.acceleration.cpu
    return False


def _matches_license(manifest: ModelManifest, license_policy: LicensePolicy) -> bool:
    license_id = manifest.upstream.license.lower()
    if license_policy in {"any", "research_only"}:
        return True
    if license_policy == "commercial_ok":
        return manifest.policy.commercial_use
    if license_policy == "permissive_only":
        return manifest.policy.commercial_use and license_id in PERMISSIVE_LICENSES
    return False


def _selection_reason(
    candidate: _Candidate,
    request: SpeechRequest,
    matched_count: int,
    *,
    benchmark_data: str,
    benchmark: BenchmarkSummary | None,
) -> str:
    parts = [
        f"selected {candidate.entry.id}",
        f"from {matched_count} matching candidate{'s' if matched_count != 1 else ''}",
        f"response_format={request.response_format}",
        f"license_policy={request.license_policy}",
        f"benchmark_data={benchmark_data}",
    ]
    if request.purpose is not None:
        parts.append(f"purpose={request.purpose}")
    if request.target_latency_ms is not None:
        parts.append(f"target_latency_ms={request.target_latency_ms}")
    if request.hardware_profile is not None:
        parts.append(f"hardware_profile={request.hardware_profile}")
    if benchmark is not None:
        parts.append(f"benchmark_ttfa_ms={benchmark.time_to_first_audio_ms:g}")
        if benchmark.hardware_profile is not None:
            parts.append(f"benchmark_profile={benchmark.hardware_profile}")
    return "; ".join(parts)


def _applied_hints(request: SpeechRequest, suite: str) -> dict[str, Any]:
    return {
        "purpose": request.purpose,
        "target_latency_ms": request.target_latency_ms,
        "license_policy": request.license_policy,
        "hardware_profile": request.hardware_profile,
        "response_format": request.response_format,
        "benchmark_suite": suite,
    }


def _candidate_benchmarks(
    candidates: list[_Candidate],
    request: SpeechRequest,
    benchmark_dir: Path | None,
    suite: str,
) -> dict[str, BenchmarkSummary]:
    results = load_benchmark_results(benchmark_dir)
    benchmarks: dict[str, BenchmarkSummary] = {}
    for candidate in candidates:
        benchmark = best_benchmark(
            results,
            model=candidate.entry.id,
            suite=suite,
            hardware_profile=request.hardware_profile,
        )
        if benchmark is not None:
            benchmarks[candidate.entry.id] = benchmark
    return benchmarks


def _benchmark_data_status(
    benchmark_dir: Path | None,
    benchmarks: dict[str, BenchmarkSummary],
    selected_benchmark: BenchmarkSummary | None,
) -> str:
    if benchmark_dir is None:
        return "not_configured"
    if selected_benchmark is not None:
        return "used"
    if benchmarks:
        return "available"
    return "missing"
