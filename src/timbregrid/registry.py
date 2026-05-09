from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from timbregrid.adapters.base import TTSAdapter
from timbregrid.adapters.fake import FakeTTSAdapter
from timbregrid.adapters.kitten import KittenTTSAdapter
from timbregrid.adapters.kokoro import KokoroAdapter
from timbregrid.models import VoiceInfo


@dataclass(frozen=True)
class ModelEntry:
    id: str
    name: str
    manifest_path: str | None
    executable: bool
    requires_extra: str | None
    adapter_factory: Callable[[], TTSAdapter] | None = None

    @property
    def available(self) -> bool:
        if not self.executable:
            return False
        if self.requires_extra is None:
            return True
        return importlib.util.find_spec(self.requires_extra) is not None

    @property
    def status(self) -> str:
        if not self.executable:
            return "manifest-only"
        if self.available:
            return "available"
        return f"missing optional dependency: {self.requires_extra}"

    def to_dict(self) -> dict:
        data = asdict(self)
        data.pop("adapter_factory", None)
        data["available"] = self.available
        data["status"] = self.status
        return data


_ROOT = Path(__file__).resolve().parents[2]
_FAKE_ADAPTER = FakeTTSAdapter()
_KITTEN_ADAPTER = KittenTTSAdapter()
_KOKORO_ADAPTER = KokoroAdapter()

_ENTRIES = {
    "fake:tts": ModelEntry(
        id="fake:tts",
        name="TimbreGrid Fake TTS",
        manifest_path=str(_ROOT / "manifests" / "fake-tts.yaml"),
        executable=True,
        requires_extra=None,
        adapter_factory=lambda: _FAKE_ADAPTER,
    ),
    "kokoro:82m": ModelEntry(
        id="kokoro:82m",
        name="Kokoro 82M",
        manifest_path=str(_ROOT / "manifests" / "kokoro-82m.yaml"),
        executable=True,
        requires_extra="kokoro",
        adapter_factory=lambda: _KOKORO_ADAPTER,
    ),
    "kitten-tts:nano-0.8": ModelEntry(
        id="kitten-tts:nano-0.8",
        name="KittenTTS Nano 0.8",
        manifest_path=str(_ROOT / "manifests" / "kitten-tts-nano-0.8.yaml"),
        executable=True,
        requires_extra="kittentts",
        adapter_factory=lambda: _KITTEN_ADAPTER,
    ),
    "chatterbox:tts": ModelEntry(
        id="chatterbox:tts",
        name="Chatterbox TTS",
        manifest_path=str(_ROOT / "manifests" / "chatterbox.yaml"),
        executable=False,
        requires_extra=None,
    ),
    "qwen3-tts:0.6b-base": ModelEntry(
        id="qwen3-tts:0.6b-base",
        name="Qwen3-TTS 12Hz 0.6B Base",
        manifest_path=str(_ROOT / "manifests" / "qwen3-tts-0.6b-base.yaml"),
        executable=False,
        requires_extra=None,
    ),
}


def list_models() -> list[ModelEntry]:
    return list(_ENTRIES.values())


def get_model_entry(model: str) -> ModelEntry:
    try:
        return _ENTRIES[model]
    except KeyError as exc:
        raise KeyError(model) from exc


def get_adapter(model: str) -> TTSAdapter:
    if model == "auto":
        return default_adapter()

    entry = get_model_entry(model)
    if entry.adapter_factory is None:
        raise KeyError(model)
    return entry.adapter_factory()


def default_adapter() -> TTSAdapter:
    return _FAKE_ADAPTER


def list_model_voices(model: str | None = None) -> list[VoiceInfo]:
    entries = [get_model_entry(model)] if model is not None else list_models()
    voices: list[VoiceInfo] = []

    for entry in entries:
        if entry.adapter_factory is None:
            continue
        for voice in entry.adapter_factory().voices():
            voices.append(_voice_for_model(voice, entry.id))

    return voices


def _voice_for_model(voice: VoiceInfo, model: str) -> VoiceInfo:
    return voice.model_copy(
        update={
            "model": voice.model or model,
            "source": voice.source or "builtin",
            "consent": voice.consent or "not_required",
        }
    )
