from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from timbregrid.manifest import ManifestError, load_manifest
from timbregrid.registry import ModelEntry, list_models


class RegistryIndexError(ValueError):
    """Raised when registry artifacts cannot be generated."""


@dataclass(frozen=True)
class RegistryArtifacts:
    index_json: str
    support_matrix_markdown: str


_ROOT = Path(__file__).resolve().parents[2]


def build_registry_artifacts(manifest_dir: Path) -> RegistryArtifacts:
    index = build_registry_index(manifest_dir)
    return RegistryArtifacts(
        index_json=render_registry_index_json(index),
        support_matrix_markdown=render_support_matrix_markdown(index),
    )


def build_registry_index(manifest_dir: Path) -> dict[str, Any]:
    manifest_paths = sorted(manifest_dir.glob("*.yaml"))
    if not manifest_paths:
        raise RegistryIndexError(f"No manifests found in {manifest_dir}")

    entries = {entry.id: entry for entry in list_models()}
    models: list[dict[str, Any]] = []
    seen: set[str] = set()

    for path in manifest_paths:
        try:
            manifest = load_manifest(path)
        except ManifestError as exc:
            raise RegistryIndexError(f"Invalid manifest {path}: {exc}") from exc
        if manifest.id in seen:
            raise RegistryIndexError(f"Duplicate manifest id: {manifest.id}")
        seen.add(manifest.id)
        models.append(
            _registry_model(
                manifest.model_dump(mode="json"),
                path,
                entries.get(manifest.id),
            )
        )

    models.sort(key=lambda model: model["id"])
    return {
        "schema_version": "0.1",
        "model_count": len(models),
        "models": models,
    }


def render_registry_index_json(index: dict[str, Any]) -> str:
    return json.dumps(index, indent=2, sort_keys=True) + "\n"


def render_support_matrix_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# TimbreGrid Model Support Matrix",
        "",
        "Generated from `manifests/*.yaml` with `uv run timbregrid registry build`.",
        "",
        "| Model | Runtime | Acceleration | Formats | Voices | Multilingual | Long-form | "
        "Streaming | Cloning | Commercial use | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for model in index["models"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{model['id']}`",
                    _runtime_label(model),
                    _acceleration_label(model["runtime"]["acceleration"]),
                    ", ".join(model["audio"]["formats"]),
                    _voices_label(model["voices"]),
                    model["capabilities"]["multilingual"],
                    model["capabilities"]["long_form"],
                    _yes_no(model["capabilities"]["streaming"]),
                    _yes_no(model["capabilities"]["voice_cloning"]),
                    _yes_no(model["policy"]["commercial_use"]),
                    model["status"],
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def write_registry_artifacts(
    manifest_dir: Path,
    index_path: Path,
    matrix_path: Path,
) -> RegistryArtifacts:
    artifacts = build_registry_artifacts(manifest_dir)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(artifacts.index_json, encoding="utf-8")
    matrix_path.write_text(artifacts.support_matrix_markdown, encoding="utf-8")
    return artifacts


def stale_registry_artifacts(
    manifest_dir: Path,
    index_path: Path,
    matrix_path: Path,
) -> list[Path]:
    artifacts = build_registry_artifacts(manifest_dir)
    stale: list[Path] = []
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != artifacts.index_json:
        stale.append(index_path)
    if (
        not matrix_path.exists()
        or matrix_path.read_text(encoding="utf-8") != artifacts.support_matrix_markdown
    ):
        stale.append(matrix_path)
    return stale


def _registry_model(
    manifest: dict[str, Any],
    manifest_path: Path,
    entry: ModelEntry | None,
) -> dict[str, Any]:
    executable = entry.executable if entry is not None else False
    requires_extra = entry.requires_extra if entry is not None else None
    available = executable and requires_extra is None

    return {
        **manifest,
        "manifest_path": _relative_path(manifest_path),
        "executable": executable,
        "requires_extra": requires_extra,
        "available": available,
        "status": _static_status(executable, requires_extra),
    }


def _static_status(executable: bool, requires_extra: str | None) -> str:
    if not executable:
        return "manifest-only"
    if requires_extra is None:
        return "available"
    return f"requires optional dependency: {requires_extra}"


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _runtime_label(model: dict[str, Any]) -> str:
    package = model["runtime"].get("package")
    if package:
        return f"{model['runtime']['kind']} / {package}"
    return model["runtime"]["kind"]


def _acceleration_label(acceleration: dict[str, Any]) -> str:
    labels: list[str] = []
    if acceleration.get("cpu"):
        labels.append("CPU")
    if acceleration.get("cuda"):
        labels.append("CUDA")
    metal = acceleration.get("metal")
    if metal == "optional":
        labels.append("Metal optional")
    elif metal:
        labels.append("Metal")
    return ", ".join(labels) if labels else "-"


def _voices_label(voices: dict[str, bool]) -> str:
    labels = []
    if voices.get("builtin"):
        labels.append("builtin")
    if voices.get("custom"):
        labels.append("custom")
    return ", ".join(labels) if labels else "-"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
