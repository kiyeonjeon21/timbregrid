from timbregrid.adapters.fake import FakeTTSAdapter
from timbregrid.adapters.kokoro import KokoroAdapter
from timbregrid.registry import get_adapter, get_model_entry, list_models


def test_registry_lists_known_models() -> None:
    ids = {entry.id for entry in list_models()}

    assert {
        "fake:tts",
        "kokoro:82m",
        "kitten-tts:nano-0.8",
        "chatterbox:tts",
        "qwen3-tts:0.6b-base",
    } <= ids


def test_registry_returns_adapters() -> None:
    assert isinstance(get_adapter("fake:tts"), FakeTTSAdapter)
    assert isinstance(get_adapter("kokoro:82m"), KokoroAdapter)


def test_kokoro_entry_exposes_optional_extra_status() -> None:
    entry = get_model_entry("kokoro:82m")
    body = entry.to_dict()

    assert body["requires_extra"] == "kokoro"
    assert body["executable"] is True
    assert body["status"]


def test_manifest_only_entries_expose_static_status() -> None:
    entry = get_model_entry("chatterbox:tts")
    body = entry.to_dict()

    assert body["requires_extra"] is None
    assert body["executable"] is False
    assert body["available"] is False
    assert body["status"] == "manifest-only"
