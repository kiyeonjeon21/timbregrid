from __future__ import annotations

from typing import Protocol

from timbregrid.models import Capabilities, SpeechRequest, SpeechResult, VoiceInfo


class AdapterError(RuntimeError):
    """Base class for adapter runtime failures."""


class AdapterDependencyError(AdapterError):
    """Raised when an optional adapter dependency is not installed."""


class TTSAdapter(Protocol):
    id: str

    def load(self) -> None: ...

    def synthesize(self, request: SpeechRequest) -> SpeechResult: ...

    def voices(self) -> list[VoiceInfo]: ...

    def capabilities(self) -> Capabilities: ...
