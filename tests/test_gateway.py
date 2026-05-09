from fastapi.testclient import TestClient

from timbregrid.gateway import create_app


def test_speech_endpoint_returns_audio_bytes() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "fake:tts",
            "input": "Hello",
            "voice": "alloy",
            "response_format": "wav",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/octet-stream")
    assert response.headers["x-timbregrid-audio-format"] == "wav"
    assert response.content.startswith(b"RIFF")


def test_speech_endpoint_rejects_missing_required_field() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={"model": "fake:tts", "input": "Hello"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["param"] == "voice"


def test_speech_endpoint_rejects_invalid_speed() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={"model": "fake:tts", "input": "Hello", "voice": "alloy", "speed": 0.1},
    )

    assert response.status_code == 400
    assert response.json()["error"]["param"] == "speed"


def test_speech_endpoint_rejects_sse_for_fake_model() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "fake:tts",
            "input": "Hello",
            "voice": "alloy",
            "stream_format": "sse",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_stream_format"
