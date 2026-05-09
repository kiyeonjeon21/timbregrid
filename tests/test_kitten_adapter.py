from types import SimpleNamespace

import pytest

from timbregrid.adapters.base import AdapterDependencyError
from timbregrid.adapters.kitten import KittenTTSAdapter
from timbregrid.models import SpeechRequest


def test_kitten_adapter_reports_missing_optional_dependency(monkeypatch) -> None:
    def missing_import(name: str):
        if name == "kittentts":
            raise ModuleNotFoundError(name)
        raise AssertionError(name)

    monkeypatch.setattr("timbregrid.adapters.kitten.importlib.import_module", missing_import)

    with pytest.raises(AdapterDependencyError, match="optional dependencies"):
        KittenTTSAdapter().load()


def test_kitten_adapter_generates_wav_with_fake_model(monkeypatch) -> None:
    class FakeKittenTTS:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def generate(self, text: str, voice: str, speed: float):
            assert text == "hello"
            assert voice == "Jasper"
            assert speed == 1.0
            return [0.0, 0.5, -0.5, 0.0]

    def fake_import(name: str):
        if name == "kittentts":
            return SimpleNamespace(KittenTTS=FakeKittenTTS)
        raise AssertionError(name)

    monkeypatch.setattr("timbregrid.adapters.kitten.importlib.import_module", fake_import)

    result = KittenTTSAdapter().synthesize(
        SpeechRequest(
            model="kitten-tts:nano-0.8",
            input="hello",
            voice="Jasper",
            response_format="wav",
        )
    )

    assert result.audio.startswith(b"RIFF")
    assert result.format == "wav"
    assert result.sample_rate_hz == 24000
    assert result.duration_ms > 0


def test_kitten_adapter_returns_pcm(monkeypatch) -> None:
    class FakeArray:
        def tolist(self):
            return [[0.0, 0.25], [-0.25, 0.0]]

    class FakeKittenTTS:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name

        def generate(self, text: str, voice: str, speed: float):
            return FakeArray()

    def fake_import(name: str):
        if name == "kittentts":
            return SimpleNamespace(KittenTTS=FakeKittenTTS)
        raise AssertionError(name)

    monkeypatch.setattr("timbregrid.adapters.kitten.importlib.import_module", fake_import)

    result = KittenTTSAdapter().synthesize(
        SpeechRequest(
            model="kitten-tts:nano-0.8",
            input="hello",
            voice="Bella",
            response_format="pcm",
        )
    )

    assert not result.audio.startswith(b"RIFF")
    assert result.format == "pcm"
    assert result.duration_ms > 0


def test_kitten_adapter_rejects_mp3() -> None:
    adapter = KittenTTSAdapter()

    with pytest.raises(ValueError, match="Unsupported response_format"):
        adapter.synthesize(
            SpeechRequest(
                model="kitten-tts:nano-0.8",
                input="hello",
                voice="Jasper",
                response_format="mp3",
            )
        )


def test_kitten_adapter_lists_builtin_voices() -> None:
    voices = {voice.id: voice for voice in KittenTTSAdapter().voices()}

    assert {"Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo"} <= set(voices)
    assert voices["Jasper"].builtin is True
    assert "kitten" in voices["Jasper"].tags
