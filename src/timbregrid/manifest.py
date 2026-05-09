from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from timbregrid.models import ModelManifest


class ManifestError(ValueError):
    """Raised when a model manifest cannot be loaded or validated."""


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
        return ModelManifest.model_validate(raw)
    except ValidationError as exc:
        raise ManifestError(str(exc)) from exc


def manifest_json_schema() -> dict[str, Any]:
    return ModelManifest.model_json_schema()
