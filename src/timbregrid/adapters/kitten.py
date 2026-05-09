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
DEFAULT_MODEL_NAME = "KittenML/kitten-tts-nano-0.8"
KITTEN_VOICES = ("Bella", "Jasper", "Luna", "Bruno", "Rosie", "Hugo", "Kiki", "Leo")
INSTALL_HINT = (
    "KittenTTS support requires optional dependencies. Install them with "
    "`uv pip install "
    "\"kittentts @ https://github.com/KittenML/KittenTTS/releases/download/0.8.1/"
    "kittentts-0.8.1-py3-none-any.whl\" \"onnxruntime<1.26\"` "
    "inside a TimbreGrid source checkout."
)


class KittenTTSAdapter:
    id = "kitten-tts:nano-0.8"

    def __init__(self, *, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def load(self) -> None:
        if self._model is not None:
            return

        try:
            kittentts = importlib.import_module("kittentts")
        except ModuleNotFoundError as exc:
            raise AdapterDependencyError(INSTALL_HINT) from exc

        try:
            self._model = kittentts.KittenTTS(self.model_name)
        except Exception as exc:  # pragma: no cover - depends on host model/cache setup.
            raise AdapterDependencyError(f"{INSTALL_HINT} KittenTTS failed to initialize: {exc}") from exc

    def voices(self) -> list[VoiceInfo]:
        return [
            VoiceInfo(id=voice, name=voice, tags=["kitten", "edge", "cpu"])
            for voice in KITTEN_VOICES
        ]

    def capabilities(self) -> Capabilities:
        return Capabilities(
            streaming=False,
            voice_cloning=False,
            multilingual="none",
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
        assert self._model is not None

        started = time.perf_counter()
        audio = self._model.generate(request.input, voice=request.voice, speed=request.speed)
        elapsed_ms = (time.perf_counter() - started) * 1000
        pcm_audio, samples = _audio_to_pcm16(audio)
        duration_ms = samples / SAMPLE_RATE_HZ * 1000 if samples else 0.0

        if request.response_format == "wav":
            output = _wrap_wav(pcm_audio)
            content_type = "audio/wav"
        else:
            output = pcm_audio
            content_type = "application/octet-stream"

        return SpeechResult(
            audio=output,
            format=request.response_format,
            content_type=content_type,
            duration_ms=duration_ms,
            sample_rate_hz=SAMPLE_RATE_HZ,
            time_to_first_audio_ms=elapsed_ms,
            model=self.id,
        )


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
