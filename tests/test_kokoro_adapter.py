from types import SimpleNamespace

import pytest

from timbregrid.adapters.base import AdapterDependencyError
from timbregrid.adapters.kokoro import KokoroAdapter
from timbregrid.models import SpeechRequest


def test_kokoro_adapter_reports_missing_optional_dependency(monkeypatch) -> None:
    def missing_import(name: str):
        if name == "kokoro":
            raise ModuleNotFoundError(name)
        raise AssertionError(name)

    monkeypatch.setattr("timbregrid.adapters.kokoro.importlib.import_module", missing_import)

    with pytest.raises(AdapterDependencyError, match="optional dependencies"):
        KokoroAdapter().load()


def test_kokoro_adapter_generates_wav_with_fake_pipeline(monkeypatch) -> None:
    class FakePipeline:
        def __init__(self, lang_code: str) -> None:
            self.lang_code = lang_code

        def __call__(self, text: str, voice: str, speed: float, split_pattern: str):
            assert text == "hello"
            assert voice == "af_heart"
            assert speed == 1.0
            assert split_pattern == r"\n+"
            yield ("hello", "HH AH L OW", [0.0, 0.5, -0.5, 0.0])

    def fake_import(name: str):
        if name == "kokoro":
            return SimpleNamespace(KPipeline=FakePipeline)
        raise AssertionError(name)

    monkeypatch.setattr("timbregrid.adapters.kokoro.importlib.import_module", fake_import)

    adapter = KokoroAdapter()
    result = adapter.synthesize(
        SpeechRequest(
            model="kokoro:82m",
            input="hello",
            voice="af_heart",
            response_format="wav",
        )
    )

    assert result.audio.startswith(b"RIFF")
    assert result.format == "wav"
    assert result.sample_rate_hz == 24000
    assert result.duration_ms > 0


def test_kokoro_adapter_accepts_result_object_audio(monkeypatch) -> None:
    class FakePipeline:
        def __init__(self, lang_code: str) -> None:
            self.lang_code = lang_code

        def __call__(self, text: str, voice: str, speed: float, split_pattern: str):
            yield SimpleNamespace(audio=[0.0, 0.25, -0.25, 0.0])

    def fake_import(name: str):
        if name == "kokoro":
            return SimpleNamespace(KPipeline=FakePipeline)
        raise AssertionError(name)

    monkeypatch.setattr("timbregrid.adapters.kokoro.importlib.import_module", fake_import)

    result = KokoroAdapter().synthesize(
        SpeechRequest(
            model="kokoro:82m",
            input="hello",
            voice="af_heart",
            response_format="wav",
        )
    )

    assert result.audio.startswith(b"RIFF")
    assert result.duration_ms > 0


def test_kokoro_adapter_rejects_mp3() -> None:
    adapter = KokoroAdapter()

    with pytest.raises(ValueError, match="Unsupported response_format"):
        adapter.synthesize(
            SpeechRequest(
                model="kokoro:82m",
                input="hello",
                voice="af_heart",
                response_format="mp3",
            )
        )
