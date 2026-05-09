from timbregrid.adapters.fake import FakeTTSAdapter
from timbregrid.adapters.kokoro import KokoroAdapter
from timbregrid.registry import get_adapter, get_model_entry, list_models


def test_registry_lists_fake_and_kokoro() -> None:
    ids = {entry.id for entry in list_models()}

    assert {"fake:tts", "kokoro:82m"} <= ids


def test_registry_returns_adapters() -> None:
    assert isinstance(get_adapter("fake:tts"), FakeTTSAdapter)
    assert isinstance(get_adapter("kokoro:82m"), KokoroAdapter)


def test_kokoro_entry_exposes_optional_extra_status() -> None:
    entry = get_model_entry("kokoro:82m")
    body = entry.to_dict()

    assert body["requires_extra"] == "kokoro"
    assert body["executable"] is True
    assert body["status"]
