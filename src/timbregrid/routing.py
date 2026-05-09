from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

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
    skipped_candidates: list[SkippedCandidate]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_model": self.requested_model,
            "selected_model": self.selected_model,
            "reason": self.reason,
            "applied_hints": self.applied_hints,
            "skipped_candidates": [candidate.to_dict() for candidate in self.skipped_candidates],
        }


@dataclass(frozen=True)
class _Candidate:
    entry: ModelEntry
    manifest: ModelManifest


def resolve_route(request: SpeechRequest, *, default_model: str = "fake:tts") -> RouteDecision:
    if request.model != "auto":
        return RouteDecision(
            requested_model=request.model,
            selected_model=request.model,
            reason="explicit model requested",
            applied_hints=_applied_hints(request),
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

    selected = sorted(matches, key=lambda candidate: _candidate_sort_key(candidate, request, default_model))[0]
    return RouteDecision(
        requested_model=request.model,
        selected_model=selected.entry.id,
        reason=_selection_reason(selected, request, len(matches)),
        applied_hints=_applied_hints(request),
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
) -> tuple[int, int, str]:
    real_adapter_score = 1 if candidate.entry.id != "fake:tts" else 0
    purpose_score = _purpose_score(candidate.manifest, request.purpose)
    default_score = 1 if candidate.entry.id == default_model else 0
    return (-real_adapter_score, -(purpose_score + default_score), candidate.entry.id)


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


def _selection_reason(candidate: _Candidate, request: SpeechRequest, matched_count: int) -> str:
    parts = [
        f"selected {candidate.entry.id}",
        f"from {matched_count} matching candidate{'s' if matched_count != 1 else ''}",
        f"response_format={request.response_format}",
        f"license_policy={request.license_policy}",
    ]
    if request.purpose is not None:
        parts.append(f"purpose={request.purpose}")
    if request.target_latency_ms is not None:
        parts.append(f"target_latency_ms={request.target_latency_ms}")
    return "; ".join(parts)


def _applied_hints(request: SpeechRequest) -> dict[str, Any]:
    return {
        "purpose": request.purpose,
        "target_latency_ms": request.target_latency_ms,
        "license_policy": request.license_policy,
        "response_format": request.response_format,
    }
