from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

import httpx


@dataclass(frozen=True)
class ConformanceCase:
    name: str
    payload: dict
    expect_success: bool


@dataclass(frozen=True)
class ConformanceResult:
    passed: int
    failed: int
    failures: list[str]

    @property
    def ok(self) -> bool:
        return self.failed == 0


CASES = [
    ConformanceCase(
        name="minimal request",
        payload={"model": "fake:tts", "input": "hello", "voice": "alloy"},
        expect_success=True,
    ),
    ConformanceCase(
        name="wav response_format",
        payload={
            "model": "fake:tts",
            "input": "hello",
            "voice": "alloy",
            "response_format": "wav",
        },
        expect_success=True,
    ),
    ConformanceCase(
        name="missing voice",
        payload={"model": "fake:tts", "input": "hello"},
        expect_success=False,
    ),
    ConformanceCase(
        name="invalid speed",
        payload={"model": "fake:tts", "input": "hello", "voice": "alloy", "speed": 0.1},
        expect_success=False,
    ),
]


def run_conformance(base_url: str, *, endpoint: str = "audio.speech") -> ConformanceResult:
    if endpoint != "audio.speech":
        raise ValueError("Only endpoint='audio.speech' is supported in the MVP")

    url = urljoin(base_url.rstrip("/") + "/", "audio/speech")
    failures: list[str] = []

    with httpx.Client(timeout=10.0) as client:
        for case in CASES:
            response = client.post(url, json=case.payload)
            success = response.status_code == 200
            if success != case.expect_success:
                failures.append(
                    f"{case.name}: expected success={case.expect_success}, "
                    f"got status={response.status_code}"
                )
                continue

            if case.expect_success and not response.content:
                failures.append(f"{case.name}: expected non-empty audio bytes")

            if not case.expect_success:
                content_type = response.headers.get("content-type", "")
                if "application/json" not in content_type:
                    failures.append(f"{case.name}: expected JSON error, got {content_type!r}")
                    continue
                body = response.json()
                if "error" not in body:
                    failures.append(f"{case.name}: expected OpenAI-shaped error body")

    return ConformanceResult(
        passed=len(CASES) - len(failures),
        failed=len(failures),
        failures=failures,
    )
