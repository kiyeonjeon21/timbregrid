from timbregrid.adapters.fake import FakeTTSAdapter
from timbregrid.models import SpeechRequest


def test_fake_adapter_returns_deterministic_wav() -> None:
    adapter = FakeTTSAdapter()
    request = SpeechRequest(
        model="fake:tts",
        input="Hello from TimbreGrid",
        voice="alloy",
        response_format="wav",
    )

    first = adapter.synthesize(request)
    second = adapter.synthesize(request)

    assert first.audio == second.audio
    assert first.audio.startswith(b"RIFF")
    assert first.sample_rate_hz == 24000
    assert first.duration_ms > 0


def test_fake_adapter_returns_pcm() -> None:
    adapter = FakeTTSAdapter()
    result = adapter.synthesize(
        SpeechRequest(
            model="fake:tts",
            input="pcm",
            voice="alloy",
            response_format="pcm",
        )
    )

    assert result.audio
    assert not result.audio.startswith(b"RIFF")
    assert result.format == "pcm"


def test_fake_adapter_returns_mp3_fixture() -> None:
    adapter = FakeTTSAdapter()
    result = adapter.synthesize(
        SpeechRequest(model="fake:tts", input="mp3", voice="alloy", response_format="mp3")
    )

    assert result.audio.startswith(b"ID3")
    assert result.content_type == "audio/mpeg"
