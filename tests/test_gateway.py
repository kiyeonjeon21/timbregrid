import json
from pathlib import Path

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


def test_speech_endpoint_rejects_unknown_voice() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "fake:tts",
            "input": "Hello",
            "voice": "missing_voice",
            "response_format": "wav",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "voice_not_found"
    assert response.json()["error"]["param"] == "voice"


def test_speech_endpoint_accepts_valid_local_catalog_voice(tmp_path: Path) -> None:
    catalog = tmp_path / "voices.json"
    catalog.write_text(
        json.dumps(
            {
                "voices": [
                    {
                        "id": "local_reference",
                        "name": "Local Reference",
                        "model": "fake:tts",
                        "builtin": False,
                        "source": "local",
                        "provenance": "Recorded by the repository owner for local testing.",
                        "consent": "granted",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(voice_catalog=catalog))

    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "fake:tts",
            "input": "Hello",
            "voice": "local_reference",
            "response_format": "wav",
        },
    )

    assert response.status_code == 200
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


def test_speech_endpoint_validates_auto_voice_after_route(monkeypatch) -> None:
    monkeypatch.setattr("timbregrid.registry.importlib.util.find_spec", lambda _: None)
    client = TestClient(create_app())

    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "auto",
            "input": "Hello",
            "voice": "Jasper",
            "response_format": "wav",
            "purpose": "realtime",
            "license_policy": "commercial_ok",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "voice_not_found"
    assert "fake:tts" in response.json()["error"]["message"]


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


def test_voices_endpoint_returns_builtin_voice_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/v1/audio/voices", params={"model": "fake:tts"})

    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "list"
    voices = {voice["id"]: voice for voice in body["data"]}
    assert voices["alloy"]["model"] == "fake:tts"
    assert voices["alloy"]["builtin"] is True
    assert voices["alloy"]["source"] == "builtin"
    assert voices["alloy"]["consent"] == "not_required"
    assert voices["alloy"]["provenance"] is None


def test_voices_endpoint_includes_local_catalog_records(tmp_path: Path) -> None:
    catalog = tmp_path / "voices.json"
    catalog.write_text(
        json.dumps(
            {
                "voices": [
                    {
                        "id": "local_reference",
                        "name": "Local Reference",
                        "model": "fake:tts",
                        "builtin": False,
                        "source": "local",
                        "language": "en-US",
                        "tags": ["test"],
                        "provenance": "Recorded by the repository owner for local testing.",
                        "consent": "granted",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app(voice_catalog=catalog))

    response = client.get("/v1/audio/voices", params={"model": "fake:tts"})

    assert response.status_code == 200
    voices = {voice["id"]: voice for voice in response.json()["data"]}
    assert voices["local_reference"]["model"] == "fake:tts"
    assert voices["local_reference"]["builtin"] is False
    assert voices["local_reference"]["source"] == "local"
    assert voices["local_reference"]["consent"] == "granted"


def test_voices_endpoint_rejects_unknown_model() -> None:
    client = TestClient(create_app())

    response = client.get("/v1/audio/voices", params={"model": "missing:model"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "model_not_found"
