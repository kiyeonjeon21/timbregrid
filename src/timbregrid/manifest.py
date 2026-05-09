from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml
from pydantic import ValidationError

from timbregrid.models import ModelManifest


class ManifestError(ValueError):
    """Raised when a model manifest cannot be loaded or validated."""


MODEL_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
LICENSE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
WEIGHT_STATUS_VALUES = {"none", "open-weight"}


def load_manifest(path: Path) -> ModelManifest:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"Could not read manifest: {path}") from exc
    except yaml.YAMLError as exc:
        raise ManifestError(f"Invalid YAML in manifest: {path}") from exc

    if not isinstance(raw, dict):
        raise ManifestError("Manifest root must be a mapping")

    try:
        manifest = ModelManifest.model_validate(raw)
    except ValidationError as exc:
        raise ManifestError(str(exc)) from exc

    _validate_manifest_semantics(manifest)
    return manifest


def manifest_json_schema() -> dict[str, Any]:
    return ModelManifest.model_json_schema()


def _validate_manifest_semantics(manifest: ModelManifest) -> None:
    if not MODEL_ID_PATTERN.fullmatch(manifest.id):
        raise ManifestError("Manifest id must use lowercase letters, numbers, dots, underscores, hyphens, or colons")

    if not _is_http_url(manifest.upstream.homepage):
        raise ManifestError("upstream.homepage must be an http(s) URL")

    license_id = manifest.upstream.license
    if not LICENSE_PATTERN.fullmatch(license_id) or license_id != license_id.lower():
        raise ManifestError("upstream.license must be a lowercase SPDX-style identifier")

    weights = manifest.upstream.weights
    if weights not in WEIGHT_STATUS_VALUES and not _is_http_url(weights):
        raise ManifestError("upstream.weights must be an http(s) URL, 'none', or 'open-weight'")

    if manifest.runtime.kind == "python" and not manifest.runtime.package:
        raise ManifestError("runtime.package is required for python runtimes")

    acceleration = manifest.runtime.acceleration
    if not (acceleration.cpu or acceleration.cuda or acceleration.metal):
        raise ManifestError("runtime.acceleration must enable at least one target")

    if not manifest.audio.formats:
        raise ManifestError("audio.formats must not be empty")
    if not manifest.capabilities.formats:
        raise ManifestError("capabilities.formats must not be empty")
    if set(manifest.audio.formats) != set(manifest.capabilities.formats):
        raise ManifestError("audio.formats and capabilities.formats must match")

    if not (manifest.voices.builtin or manifest.voices.custom):
        raise ManifestError("voices must declare builtin or custom support")

    if manifest.capabilities.voice_cloning and not manifest.voices.custom:
        raise ManifestError("voice_cloning requires voices.custom=true")
    if manifest.capabilities.voice_cloning and not manifest.policy.requires_voice_consent:
        raise ManifestError("voice_cloning requires policy.requires_voice_consent=true")
    if manifest.voices.custom and not manifest.policy.requires_voice_consent:
        raise ManifestError("custom voices require policy.requires_voice_consent=true")


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
