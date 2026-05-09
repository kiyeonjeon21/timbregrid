from __future__ import annotations

import base64
import hashlib
import io
import math
import struct
import wave

from timbregrid.models import Capabilities, SpeechRequest, SpeechResult, VoiceInfo


SAMPLE_RATE_HZ = 24_000
SUPPORTED_FORMATS = {"mp3", "wav", "pcm"}
SILENT_MP3_BASE64 = (
    "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjYyLjEyLjEwMAAAAAAAAAAAAAAA//OEwAAAAAAAAAAAAElu"
    "Zm8AAAAPAAAACQAAAZgAh4eHh4eHh4eHh4eWlpaWlpaWlpaWlqWlpaWlpaWlpaWltLS0tLS0tLS0"
    "tLTDw8PDw8PDw8PDw9LS0tLS0tLS0tLS4eHh4eHh4eHh4eHw8PDw8PDw8PDw8P//////////////"
    "AAAAAExhdmM2Mi4yOAAAAAAAAAAAAAAAACQD8AAAAAAAAAGYz6dW+wAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAA//MUxAAAAANIAAAAAExBTUUzLjEwMFVV//MUxAsAAANIAAAAAFVVVVVVVVVVVVVV//MUxBYA"
    "AANIAAAAAFVVVVVVVVVVVVVV//MUxCEAAANIAAAAAFVVVVVVVVVVVVVV//MUxCwAAANIAAAAAFVVVVV"
    "VVVVVVVVV//MUxDcAAANIAAAAAFVVVVVVVVVVVVVV//MUxEIAAANIAAAAAFVVVVVVVVVVVVVV//MUxE"
    "0AAANIAAAAAFVVVVVVVVVVVVVV//MUxFgAAANIAAAAAFVVVVVVVVVVVVVV"
)


class FakeTTSAdapter:
    id = "fake:tts"

    def load(self) -> None:
        return None

    def voices(self) -> list[VoiceInfo]:
        return [
            VoiceInfo(id="alloy", name="Alloy"),
            VoiceInfo(id="coral", name="Coral"),
            VoiceInfo(id="af_heart", name="AF Heart"),
        ]

    def capabilities(self) -> Capabilities:
        return Capabilities(
            streaming=False,
            voice_cloning=False,
            multilingual="limited",
            long_form="limited",
            style_control="speed",
            formats=["mp3", "wav", "pcm"],
        )

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        if request.response_format not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported response_format: {request.response_format}")

        duration_ms = _duration_ms(request.input, request.speed)
        pcm = _generate_pcm(request, duration_ms)

        if request.response_format == "pcm":
            audio = pcm
            content_type = "application/octet-stream"
        elif request.response_format == "wav":
            audio = _wrap_wav(pcm)
            content_type = "audio/wav"
        else:
            audio = base64.b64decode(SILENT_MP3_BASE64)
            content_type = "audio/mpeg"

        return SpeechResult(
            audio=audio,
            format=request.response_format,
            content_type=content_type,
            duration_ms=duration_ms,
            sample_rate_hz=SAMPLE_RATE_HZ,
            time_to_first_audio_ms=0.0,
            model=self.id,
        )


def _duration_ms(text: str, speed: float) -> float:
    base = 280 + min(len(text), 120) * 18
    return max(180.0, min(2_500.0, base / speed))


def _generate_pcm(request: SpeechRequest, duration_ms: float) -> bytes:
    seed = "|".join(
        [
            request.model,
            request.voice,
            request.input,
            request.instructions or "",
            f"{request.speed:.3f}",
        ]
    )
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    frequency = 220 + digest[0]
    phase = digest[1] / 255 * math.tau
    total_samples = int(SAMPLE_RATE_HZ * duration_ms / 1000)
    frames = bytearray()

    for index in range(total_samples):
        t = index / SAMPLE_RATE_HZ
        fade = min(1.0, index / 400, (total_samples - index) / 400)
        sample = math.sin(math.tau * frequency * t + phase) * fade * 0.18
        frames.extend(struct.pack("<h", int(sample * 32767)))

    return bytes(frames)


def _wrap_wav(pcm: bytes) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE_HZ)
        wav.writeframes(pcm)
    return buffer.getvalue()
