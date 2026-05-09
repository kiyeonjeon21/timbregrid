from __future__ import annotations

import importlib
import io
import struct
import time
import wave
from collections.abc import Iterable
from typing import Any

from timbregrid.adapters.base import AdapterDependencyError
from timbregrid.models import Capabilities, SpeechRequest, SpeechResult, VoiceInfo


SAMPLE_RATE_HZ = 24_000
SUPPORTED_FORMATS = {"wav", "pcm"}
INSTALL_HINT = (
    "Kokoro support requires optional dependencies. Install them with "
    "`uv sync --extra kokoro` or `pip install 'timbregrid[kokoro]'`, and install "
    "the system `espeak-ng` package if your platform requires it."
)


class KokoroAdapter:
    id = "kokoro:82m"

    def __init__(self, *, lang_code: str = "a") -> None:
        self.lang_code = lang_code
        self._pipeline: Any | None = None

    def load(self) -> None:
        if self._pipeline is not None:
            return

        try:
            kokoro = importlib.import_module("kokoro")
        except ModuleNotFoundError as exc:
            raise AdapterDependencyError(INSTALL_HINT) from exc

        try:
            self._pipeline = kokoro.KPipeline(lang_code=self.lang_code)
        except Exception as exc:  # pragma: no cover - depends on host espeak/model setup.
            raise AdapterDependencyError(f"{INSTALL_HINT} Kokoro failed to initialize: {exc}") from exc

    def voices(self) -> list[VoiceInfo]:
        return [
            VoiceInfo(id="af_heart", name="AF Heart", language="en-US", tags=["kokoro"]),
            VoiceInfo(id="af_bella", name="AF Bella", language="en-US", tags=["kokoro"]),
            VoiceInfo(id="af_nicole", name="AF Nicole", language="en-US", tags=["kokoro"]),
            VoiceInfo(id="am_adam", name="AM Adam", language="en-US", tags=["kokoro"]),
        ]

    def capabilities(self) -> Capabilities:
        return Capabilities(
            streaming=False,
            voice_cloning=False,
            multilingual="limited",
            long_form="limited",
            style_control="speed",
            formats=["wav", "pcm"],
        )

    def synthesize(self, request: SpeechRequest) -> SpeechResult:
        if request.response_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported response_format for {self.id}: {request.response_format}. "
                "Supported formats: wav, pcm"
            )

        self.load()
        assert self._pipeline is not None

        started = time.perf_counter()
        chunks: list[bytes] = []
        first_audio_ms: float | None = None
        total_samples = 0

        generator = self._pipeline(
            request.input,
            voice=request.voice,
            speed=request.speed,
            split_pattern=r"\n+",
        )

        for item in generator:
            audio = _pipeline_audio(item)
            pcm, samples = _audio_to_pcm16(audio)
            if samples == 0:
                continue
            if first_audio_ms is None:
                first_audio_ms = (time.perf_counter() - started) * 1000
            chunks.append(pcm)
            total_samples += samples

        pcm_audio = b"".join(chunks)
        duration_ms = total_samples / SAMPLE_RATE_HZ * 1000 if total_samples else 0.0
        if request.response_format == "wav":
            audio = _wrap_wav(pcm_audio)
            content_type = "audio/wav"
        else:
            audio = pcm_audio
            content_type = "application/octet-stream"

        return SpeechResult(
            audio=audio,
            format=request.response_format,
            content_type=content_type,
            duration_ms=duration_ms,
            sample_rate_hz=SAMPLE_RATE_HZ,
            time_to_first_audio_ms=first_audio_ms or 0.0,
            model=self.id,
        )


def _pipeline_audio(item: Any) -> Any:
    audio = getattr(item, "audio", None)
    if audio is not None:
        return audio
    if isinstance(item, tuple) and len(item) >= 3:
        return item[2]
    return item


def _audio_to_pcm16(audio: Any) -> tuple[bytes, int]:
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()

    values = list(_flatten(audio.tolist() if hasattr(audio, "tolist") else audio))
    frames = bytearray()
    for value in values:
        sample = max(-1.0, min(1.0, float(value)))
        frames.extend(struct.pack("<h", int(sample * 32767)))
    return bytes(frames), len(values)


def _flatten(value: Any) -> Iterable[float]:
    if isinstance(value, (bytes, bytearray, str)):
        raise TypeError("Audio samples must be numeric")
    try:
        iterator = iter(value)
    except TypeError:
        yield value
        return

    for item in iterator:
        if isinstance(item, (list, tuple)) or (
            not isinstance(item, (str, bytes, bytearray)) and hasattr(item, "__iter__")
        ):
            yield from _flatten(item)
        else:
            yield item


def _wrap_wav(pcm: bytes) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE_HZ)
        wav.writeframes(pcm)
    return buffer.getvalue()
