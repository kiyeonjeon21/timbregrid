import socket
import threading
import time

import uvicorn

from timbregrid.conformance import build_speech_cases, run_conformance
from timbregrid.gateway import create_app


def test_build_speech_cases_uses_configured_model_voice_and_format() -> None:
    cases = build_speech_cases(model="custom:model", voice="custom_voice", response_format="pcm")

    configured = next(case for case in cases if case.name == "configured response_format")
    assert configured.payload["model"] == "custom:model"
    assert configured.payload["voice"] == "custom_voice"
    assert configured.payload["response_format"] == "pcm"

    missing_model = next(case for case in cases if case.name == "missing model")
    assert "model" not in missing_model.payload


def test_run_conformance_against_fake_gateway() -> None:
    server, thread, port = _start_server()
    try:
        report = run_conformance(
            f"http://127.0.0.1:{port}/v1",
            model="fake:tts",
            voice="alloy",
            response_format="wav",
            timeout=5,
        )
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    assert report.ok
    assert report.summary["total"] == 11
    assert report.summary["passed"] == 11
    assert report.summary["failed"] == 0
    assert report.config["model"] == "fake:tts"
    assert all(case.request_payload for case in report.cases)


def _start_server() -> tuple[uvicorn.Server, threading.Thread, int]:
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(),
            host="127.0.0.1",
            port=port,
            log_level="error",
            access_log=False,
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started
    return server, thread, port


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
