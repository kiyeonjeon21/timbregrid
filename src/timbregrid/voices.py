from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from timbregrid.models import VoiceInfo


class VoiceCatalogError(ValueError):
    """Raised when a local voice catalog cannot be loaded safely."""


class VoiceCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voices: list[VoiceInfo] = Field(default_factory=list)


def load_voice_catalog(path: Path | None) -> list[VoiceInfo]:
    if path is None:
        return []
    if not path.exists():
        raise VoiceCatalogError(f"Voice catalog was not found: {path}")
    if path.is_dir():
        raise VoiceCatalogError(f"Voice catalog must be a JSON file: {path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        catalog = VoiceCatalog.model_validate(raw)
    except json.JSONDecodeError as exc:
        raise VoiceCatalogError(f"Invalid voice catalog JSON: {exc}") from exc
    except ValidationError as exc:
        raise VoiceCatalogError(f"Invalid voice catalog: {exc}") from exc
    except OSError as exc:
        raise VoiceCatalogError(f"Could not read voice catalog {path}: {exc}") from exc

    _validate_catalog_voices(catalog.voices)
    return catalog.voices


def merge_voices(builtin_voices: Iterable[VoiceInfo], catalog_voices: Iterable[VoiceInfo]) -> list[VoiceInfo]:
    merged: list[VoiceInfo] = []
    seen: set[tuple[str, str]] = set()

    for voice in [*builtin_voices, *catalog_voices]:
        if voice.model is None:
            raise VoiceCatalogError(f"Voice '{voice.id}' is missing model metadata")
        key = (voice.model, voice.id)
        if key in seen:
            raise VoiceCatalogError(f"Duplicate voice '{voice.id}' for model '{voice.model}'")
        seen.add(key)
        merged.append(voice)

    return merged


def filter_voices(voices: Iterable[VoiceInfo], model: str | None) -> list[VoiceInfo]:
    if model is None:
        return list(voices)
    return [voice for voice in voices if voice.model == model]


def _validate_catalog_voices(voices: list[VoiceInfo]) -> None:
    seen: set[tuple[str, str]] = set()
    for voice in voices:
        if voice.model is None:
            raise VoiceCatalogError(f"Voice '{voice.id}' is missing model metadata")

        key = (voice.model, voice.id)
        if key in seen:
            raise VoiceCatalogError(f"Duplicate voice '{voice.id}' for model '{voice.model}'")
        seen.add(key)

        if not voice.builtin and voice.source == "builtin":
            raise VoiceCatalogError(
                f"Voice '{voice.id}' for model '{voice.model}' requires source='local' or source='custom'"
            )
        if voice.builtin and voice.source in {"local", "custom"}:
            raise VoiceCatalogError(
                f"Voice '{voice.id}' for model '{voice.model}' with source='{voice.source}' must set builtin=false"
            )

        if _requires_consent_record(voice):
            if voice.consent != "granted":
                raise VoiceCatalogError(
                    f"Voice '{voice.id}' for model '{voice.model}' requires consent='granted'"
                )
            if voice.provenance is None or not voice.provenance.strip():
                raise VoiceCatalogError(
                    f"Voice '{voice.id}' for model '{voice.model}' requires provenance"
                )


def _requires_consent_record(voice: VoiceInfo) -> bool:
    return not voice.builtin or voice.source in {"local", "custom"}
