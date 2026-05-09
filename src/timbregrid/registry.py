from __future__ import annotations

import importlib.util
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from timbregrid.adapters.base import TTSAdapter
from timbregrid.adapters.fake import FakeTTSAdapter
from timbregrid.adapters.kokoro import KokoroAdapter


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
