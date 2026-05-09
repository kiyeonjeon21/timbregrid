from __future__ import annotations

import os
from pathlib import Path

from openai import OpenAI


def main() -> None:
    base_url = os.environ.get("TIMBREGRID_BASE_URL", "http://127.0.0.1:8889/v1")
    model = os.environ.get("TIMBREGRID_MODEL", "fake:tts")
    voice = os.environ.get("TIMBREGRID_VOICE", "alloy")
    response_format = os.environ.get("TIMBREGRID_RESPONSE_FORMAT", "wav")
    text = os.environ.get("TIMBREGRID_INPUT", "Hello from the OpenAI Python SDK.")
    output = Path(os.environ.get("TIMBREGRID_OUTPUT", "speech.wav"))

    client = OpenAI(base_url=base_url, api_key=os.environ.get("OPENAI_API_KEY", "local"))
    response = client.audio.speech.create(
        model=model,
        input=text,
        voice=voice,
        response_format=response_format,
    )

    audio = response.read()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(audio)
    print(f"Wrote {output} ({len(audio)} bytes)")


if __name__ == "__main__":
    main()
