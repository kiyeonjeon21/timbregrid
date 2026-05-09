from __future__ import annotations

from timbregrid.adapters.base import TTSAdapter
from timbregrid.adapters.fake import FakeTTSAdapter


_FAKE_ADAPTER = FakeTTSAdapter()


def get_adapter(model: str) -> TTSAdapter:
    if model in {"auto", "fake:tts"}:
        return _FAKE_ADAPTER
    raise KeyError(model)


def default_adapter() -> TTSAdapter:
    return _FAKE_ADAPTER
