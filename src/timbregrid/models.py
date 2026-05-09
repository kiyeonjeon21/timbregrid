from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


AudioFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]
SupportedFakeFormat = Literal["mp3", "wav", "pcm"]
RoutingPurpose = Literal["realtime", "narration", "cloning", "dialogue", "edge", "multilingual"]
LicensePolicy = Literal["any", "commercial_ok", "permissive_only", "research_only"]
VoiceSource = Literal["builtin", "local", "custom"]
VoiceConsent = Literal["not_required", "granted", "unknown"]


class Acceleration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cpu: bool = False
    cuda: bool = False
    metal: bool | Literal["optional"] = False


class Upstream(BaseModel):
    model_config = ConfigDict(extra="forbid")

    homepage: str
    license: str
    weights: str


class Runtime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    package: str | None = None
    acceleration: Acceleration = Field(default_factory=Acceleration)


class Capabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")

    streaming: bool = False
    voice_cloning: bool = False
    multilingual: Literal["none", "limited", "full"] = "none"
    long_form: Literal["none", "limited", "full"] = "none"
    style_control: str | list[str] | None = None
    formats: list[AudioFormat] = Field(default_factory=lambda: ["mp3", "wav", "pcm"])


class Audio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_rate_hz: Annotated[int, Field(gt=0)]
    formats: list[AudioFormat]


class Voices(BaseModel):
    model_config = ConfigDict(extra="forbid")

    builtin: bool = False
    custom: bool = False


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commercial_use: bool = False
    requires_voice_consent: bool = False


class ModelManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"]
    id: str
    name: str
    upstream: Upstream
    runtime: Runtime
    capabilities: Capabilities
    audio: Audio
    voices: Voices
    policy: Policy
    notes: list[str] = Field(default_factory=list)


class VoiceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    model: Annotated[str | None, Field(min_length=1)] = None
    builtin: bool = True
    language: str | None = None
    tags: list[str] = Field(default_factory=list)
    source: VoiceSource = "builtin"
    provenance: str | None = None
    consent: VoiceConsent = "not_required"


class SpeechRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    input: Annotated[str, Field(min_length=1)]
    voice: str
    response_format: AudioFormat = "mp3"
    speed: Annotated[float, Field(ge=0.25, le=4.0)] = 1.0
    stream_format: str | None = None
    instructions: str | None = None
    purpose: RoutingPurpose | None = None
    target_latency_ms: Annotated[int | None, Field(gt=0)] = None
    license_policy: LicensePolicy = "any"
    hardware_profile: str | None = None

    @field_validator("stream_format")
    @classmethod
    def validate_stream_format(cls, value: str | None) -> str | None:
        if value is None or value == "sse":
            return value
        raise ValueError("stream_format must be 'sse' when provided")


class SpeechResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    audio: bytes
    format: AudioFormat
    content_type: str
    duration_ms: float
    sample_rate_hz: int
    time_to_first_audio_ms: float
    model: str


class BenchmarkRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    ok: bool
    error: str | None = None
    total_generation_ms: float | None = None
    time_to_first_audio_ms: float | None = None
    real_time_factor: float | None = None
    memory_peak_bytes: int | None = None
    output_duration_ms: float | None = None
    sample_rate_hz: int | None = None
    format: AudioFormat | None = None


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1"] = "0.1"
    model: str
    suite: str
    created_at: str
    hardware: dict[str, Any]
    metrics: dict[str, float | int]
    runs: list[BenchmarkRun]
