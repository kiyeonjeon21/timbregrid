from __future__ import annotations

from dataclasses import dataclass

from timbregrid.models import RoutingPurpose


@dataclass(frozen=True)
class BenchmarkSuite:
    id: str
    purpose: RoutingPurpose
    description: str
    prompts: tuple[str, ...]


BENCHMARK_SUITES: tuple[BenchmarkSuite, ...] = (
    BenchmarkSuite(
        id="realtime-agent",
        purpose="realtime",
        description="Short utterances for low-latency assistant responses.",
        prompts=(
            "Hello from a local open-source TTS runtime.",
            "Your meeting starts in five minutes.",
            "I can help compare latency, voice support, and licensing.",
        ),
    ),
    BenchmarkSuite(
        id="narration",
        purpose="narration",
        description="Longer passages for audiobook, article, and explainer narration.",
        prompts=(
            "Chapter one begins with a quiet room, a ticking clock, and a decision that cannot wait.",
            "The city woke slowly as the first train crossed the bridge and the market lights came on.",
            "For the listener, a clear narration voice should keep pace, emphasis, and tone stable.",
        ),
    ),
    BenchmarkSuite(
        id="multilingual",
        purpose="multilingual",
        description="Mixed-language prompts for pronunciation and language-switch stability.",
        prompts=(
            "Hello, hola, 안녕하세요. Welcome to the multilingual speech test.",
            "오늘 회의는 오후 세시에 시작합니다. Please join from the main conference room.",
            "Bonjour. This passage switches from French to English, then says ありがとうございます.",
        ),
    ),
    BenchmarkSuite(
        id="cloning",
        purpose="cloning",
        description="Voice consistency prompts for models evaluated with a separate reference voice.",
        prompts=(
            "Please preserve the speaker's calm tone while reading this short sample.",
            "My voice should stay consistent across names, numbers, and pauses.",
            "The reference speaker says local models need consent-aware evaluation.",
        ),
    ),
    BenchmarkSuite(
        id="dialogue",
        purpose="dialogue",
        description="Multi-turn and multi-speaker text for dialogue-oriented synthesis.",
        prompts=(
            "Alex: Can you hear the low-latency voice?\nMina: Yes, the response feels immediate.",
            "Host: Welcome back to the local speech lab.\nGuest: Today we compare expressive open models.",
            "Narrator: The door opened.\nSpeaker one: We should leave now.\nSpeaker two: Not without the map.",
        ),
    ),
)

_SUITES_BY_ID = {suite.id: suite for suite in BENCHMARK_SUITES}


def list_benchmark_suites() -> tuple[BenchmarkSuite, ...]:
    return BENCHMARK_SUITES


def benchmark_suite_ids() -> tuple[str, ...]:
    return tuple(suite.id for suite in BENCHMARK_SUITES)


def get_benchmark_suite(suite_id: str) -> BenchmarkSuite:
    suite = _SUITES_BY_ID.get(suite_id)
    if suite is None:
        available = ", ".join(benchmark_suite_ids())
        raise ValueError(f"Unknown benchmark suite: {suite_id}. Available suites: {available}")
    return suite
