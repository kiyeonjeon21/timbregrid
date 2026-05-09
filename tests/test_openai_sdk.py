import socket
import threading
import time

import pytest
import uvicorn

from timbregrid.gateway import create_app


def test_openai_python_sdk_can_read_speech_response() -> None:
    openai = pytest.importorskip("openai")
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

    try:
        deadline = time.time() + 5
        while not server.started and time.time() < deadline:
            time.sleep(0.05)
        assert server.started

        client = openai.OpenAI(base_url=f"http://127.0.0.1:{port}/v1", api_key="local")
        speech = client.audio.speech.create(
            model="fake:tts",
            input="Hello from the OpenAI SDK",
            voice="alloy",
            response_format="wav",
        )

        assert speech.read().startswith(b"RIFF")
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])
