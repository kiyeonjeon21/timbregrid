from __future__ import annotations

import json
import platform
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

from timbregrid.models import BenchmarkResult, BenchmarkRun, SpeechRequest
from timbregrid.registry import get_adapter


PROMPT_SUITES = {
    "realtime-agent": [
        "Hello from a local open-source TTS runtime.",
        "Your meeting starts in five minutes.",
        "I can help compare latency, voice support, and licensing.",
    ]
}


def run_benchmark(
    model: str,
    *,
    suite: str = "realtime-agent",
    response_format: str = "wav",
    voice: str | None = None,
) -> BenchmarkResult:
    if suite not in PROMPT_SUITES:
        raise ValueError(f"Unknown benchmark suite: {suite}")

    adapter = get_adapter(model)
    adapter.load()
    selected_voice = voice or _default_voice(adapter)
    runs: list[BenchmarkRun] = []

    for prompt in PROMPT_SUITES[suite]:
        tracemalloc.start()
        started = time.perf_counter()
        try:
            request = SpeechRequest(
                model=model,
                input=prompt,
                voice=selected_voice,
                response_format=response_format,
            )
            result = adapter.synthesize(request)
            elapsed_ms = (time.perf_counter() - started) * 1000
            _, peak = tracemalloc.get_traced_memory()
            real_time_factor = elapsed_ms / result.duration_ms if result.duration_ms else 0.0
            runs.append(
                BenchmarkRun(
                    prompt=prompt,
                    ok=True,
                    total_generation_ms=elapsed_ms,
                    time_to_first_audio_ms=result.time_to_first_audio_ms,
                    real_time_factor=real_time_factor,
                    memory_peak_bytes=peak,
                    output_duration_ms=result.duration_ms,
                    sample_rate_hz=result.sample_rate_hz,
                    format=result.format,
                )
            )
        except Exception as exc:  # pragma: no cover - exercised by external adapters later.
            elapsed_ms = (time.perf_counter() - started) * 1000
            _, peak = tracemalloc.get_traced_memory()
            runs.append(
                BenchmarkRun(
                    prompt=prompt,
                    ok=False,
                    error=str(exc),
                    total_generation_ms=elapsed_ms,
                    memory_peak_bytes=peak,
                )
            )
        finally:
            tracemalloc.stop()

    return BenchmarkResult(
        model=model,
        suite=suite,
        created_at=datetime.now(timezone.utc).isoformat(),
        hardware=_hardware_profile(),
        metrics=_aggregate_metrics(runs),
        runs=runs,
    )


def write_benchmark(result: BenchmarkResult, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _hardware_profile() -> dict[str, str]:
    return {
        "os": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
    }


def _default_voice(adapter) -> str:
    voices = adapter.voices()
    return voices[0].id if voices else "alloy"


def _aggregate_metrics(runs: list[BenchmarkRun]) -> dict[str, float | int]:
    ok_runs = [run for run in runs if run.ok]
    failures = len(runs) - len(ok_runs)

    def avg(name: str) -> float:
        values = [getattr(run, name) for run in ok_runs if getattr(run, name) is not None]
        return float(sum(values) / len(values)) if values else 0.0

    return {
        "runs": len(runs),
        "failures": failures,
        "failure_rate": failures / len(runs) if runs else 0.0,
        "time_to_first_audio_ms": avg("time_to_first_audio_ms"),
        "total_generation_ms": avg("total_generation_ms"),
        "real_time_factor": avg("real_time_factor"),
        "memory_peak_bytes": int(max((run.memory_peak_bytes or 0 for run in runs), default=0)),
        "output_duration_ms": avg("output_duration_ms"),
    }
