import pytest
from pathlib import Path

from timbregrid.models import SpeechRequest
from timbregrid.routing import RouteNotFound, resolve_route


def test_explicit_model_route_passes_through() -> None:
    decision = resolve_route(_request(model="kokoro:82m"))

    assert decision.selected_model == "kokoro:82m"
    assert decision.reason == "explicit model requested"


def test_auto_selects_fake_when_kokoro_dependency_is_missing(monkeypatch) -> None:
    _mock_find_spec(monkeypatch, kokoro_available=False)

    decision = resolve_route(_request(purpose="realtime", license_policy="commercial_ok"))

    assert decision.selected_model == "fake:tts"
    assert any(candidate.model == "kokoro:82m" for candidate in decision.skipped_candidates)


def test_auto_prefers_real_adapter_when_available(monkeypatch) -> None:
    _mock_find_spec(monkeypatch, kokoro_available=True)

    decision = resolve_route(_request(response_format="wav", purpose="realtime"))

    assert decision.selected_model == "kokoro:82m"
    assert decision.benchmark_data == "not_configured"


def test_auto_uses_benchmark_when_target_latency_is_requested(monkeypatch) -> None:
    _mock_find_spec(monkeypatch, kokoro_available=True)

    decision = resolve_route(
        _request(response_format="wav", purpose="realtime", target_latency_ms=350),
        benchmark_dir=Path("benchmarks/examples"),
    )

    assert decision.selected_model == "fake:tts"
    assert decision.benchmark_data == "used"
    assert decision.selected_benchmark is not None
    assert decision.selected_benchmark.time_to_first_audio_ms == 0.0


def test_auto_filters_benchmarks_by_hardware_profile(monkeypatch) -> None:
    _mock_find_spec(monkeypatch, kokoro_available=True)

    decision = resolve_route(
        _request(
            response_format="wav",
            purpose="realtime",
            target_latency_ms=350,
            hardware_profile="missing-profile",
        ),
        benchmark_dir=Path("benchmarks/examples"),
    )

    assert decision.selected_model == "kokoro:82m"
    assert decision.benchmark_data == "missing"


def test_auto_filters_by_response_format(monkeypatch) -> None:
    _mock_find_spec(monkeypatch, kokoro_available=True)

    decision = resolve_route(_request(response_format="mp3"))

    assert decision.selected_model == "fake:tts"
    assert any(
        candidate.model == "kokoro:82m" and "response_format=mp3" in candidate.reason
        for candidate in decision.skipped_candidates
    )


def test_auto_accepts_current_license_policies(monkeypatch) -> None:
    _mock_find_spec(monkeypatch, kokoro_available=False)

    commercial = resolve_route(_request(license_policy="commercial_ok"))
    permissive = resolve_route(_request(license_policy="permissive_only"))

    assert commercial.selected_model == "fake:tts"
    assert permissive.selected_model == "fake:tts"


def test_auto_returns_no_route_for_cloning(monkeypatch) -> None:
    _mock_find_spec(monkeypatch, kokoro_available=True)

    with pytest.raises(RouteNotFound) as exc_info:
        resolve_route(_request(purpose="cloning"))

    assert "No route found" in str(exc_info.value)
    skipped_models = {candidate.model for candidate in exc_info.value.skipped_candidates}
    assert skipped_models >= {
        "fake:tts",
        "kokoro:82m",
        "chatterbox:tts",
        "qwen3-tts:0.6b-base",
    }


def _request(**updates) -> SpeechRequest:
    payload = {
        "model": "auto",
        "input": "Hello",
        "voice": "alloy",
        "response_format": "wav",
    }
    payload.update(updates)
    return SpeechRequest(**payload)


def _mock_find_spec(monkeypatch, *, kokoro_available: bool) -> None:
    def find_spec(name: str):
        if name == "kokoro" and kokoro_available:
            return object()
        return None

    monkeypatch.setattr("timbregrid.registry.importlib.util.find_spec", find_spec)
