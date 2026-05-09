import json
from pathlib import Path

import pytest

from timbregrid.models import VoiceInfo
from timbregrid.voices import (
    VoiceCatalogError,
    VoiceConsentError,
    load_voice_catalog,
    merge_voices,
    validate_voice_consent,
)


def test_load_voice_catalog_accepts_local_voice_with_consent(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path,
        [
            {
                "id": "voice_a",
                "name": "Voice A",
                "model": "fake:tts",
                "builtin": False,
                "source": "local",
                "provenance": "Recorded locally by the user.",
                "consent": "granted",
            }
        ],
    )

    voices = load_voice_catalog(path)

    assert voices == [
        VoiceInfo(
            id="voice_a",
            name="Voice A",
            model="fake:tts",
            builtin=False,
            source="local",
            provenance="Recorded locally by the user.",
            consent="granted",
        )
    ]


def test_load_voice_catalog_requires_provenance_for_local_voice(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path,
        [
            {
                "id": "voice_a",
                "name": "Voice A",
                "model": "fake:tts",
                "builtin": False,
                "source": "local",
                "consent": "granted",
            }
        ],
    )

    with pytest.raises(VoiceCatalogError, match="requires provenance"):
        load_voice_catalog(path)


def test_load_voice_catalog_requires_granted_consent_for_local_voice(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path,
        [
            {
                "id": "voice_a",
                "name": "Voice A",
                "model": "fake:tts",
                "builtin": False,
                "source": "local",
                "provenance": "Recorded locally by the user.",
                "consent": "unknown",
            }
        ],
    )

    with pytest.raises(VoiceCatalogError, match="requires consent='granted'"):
        load_voice_catalog(path)


def test_load_voice_catalog_requires_source_for_non_builtin_voice(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path,
        [
            {
                "id": "voice_a",
                "name": "Voice A",
                "model": "fake:tts",
                "builtin": False,
                "provenance": "Recorded locally by the user.",
                "consent": "granted",
            }
        ],
    )

    with pytest.raises(VoiceCatalogError, match="requires source='local' or source='custom'"):
        load_voice_catalog(path)


def test_load_voice_catalog_rejects_duplicate_model_voice_pairs(tmp_path: Path) -> None:
    path = _write_catalog(
        tmp_path,
        [
            {
                "id": "voice_a",
                "name": "Voice A",
                "model": "fake:tts",
                "builtin": True,
            },
            {
                "id": "voice_a",
                "name": "Voice A Duplicate",
                "model": "fake:tts",
                "builtin": True,
            },
        ],
    )

    with pytest.raises(VoiceCatalogError, match="Duplicate voice 'voice_a'"):
        load_voice_catalog(path)


def test_load_voice_catalog_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(VoiceCatalogError, match="was not found"):
        load_voice_catalog(tmp_path / "missing.json")


def test_merge_voices_rejects_builtin_catalog_duplicate() -> None:
    builtin = [VoiceInfo(id="alloy", name="Alloy", model="fake:tts")]
    catalog = [
        VoiceInfo(
            id="alloy",
            name="Local Alloy",
            model="fake:tts",
            builtin=False,
            source="local",
            provenance="Recorded locally by the user.",
            consent="granted",
        )
    ]

    with pytest.raises(VoiceCatalogError, match="Duplicate voice 'alloy'"):
        merge_voices(builtin, catalog)


def test_validate_voice_consent_rejects_invalid_runtime_voice() -> None:
    voice = VoiceInfo(
        id="voice_a",
        name="Voice A",
        model="fake:tts",
        builtin=False,
        source="local",
        provenance="Recorded locally by the user.",
        consent="unknown",
    )

    with pytest.raises(VoiceConsentError, match="requires consent='granted'"):
        validate_voice_consent(voice)


def _write_catalog(tmp_path: Path, voices: list[dict]) -> Path:
    path = tmp_path / "voices.json"
    path.write_text(json.dumps({"voices": voices}), encoding="utf-8")
    return path
