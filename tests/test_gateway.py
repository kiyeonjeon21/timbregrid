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


def test_speech_endpoint_routes_auto_to_available_model(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.registry.importlib.util.find_spec", lambda _: None)
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "auto",
            "input": "Hello",
            "voice": "alloy",
            "response_format": "wav",
            "purpose": "realtime",
            "license_policy": "commercial_ok",
        },
    )

    assert response.status_code == 200
    assert response.headers["x-timbregrid-model"] == "fake:tts"
    assert "selected fake:tts" in response.headers["x-timbregrid-route-reason"]
    assert "benchmark_data=used" in response.headers["x-timbregrid-route-reason"]


def test_speech_endpoint_returns_no_route_for_auto(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.registry.importlib.util.find_spec", lambda _: None)
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "auto",
            "input": "Hello",
            "voice": "alloy",
            "response_format": "wav",
            "purpose": "cloning",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "no_route_found"


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
