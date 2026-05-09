import pytest

from timbregrid.bench import run_benchmark
from timbregrid.benchmark_suites import (
    benchmark_suite_ids,
    get_benchmark_suite,
    list_benchmark_suites,
)


EXPECTED_SUITES = {
    "realtime-agent",
    "narration",
    "multilingual",
    "cloning",
    "dialogue",
}


def test_all_roadmap_benchmark_suites_are_defined() -> None:
    assert set(benchmark_suite_ids()) == EXPECTED_SUITES


def test_benchmark_suites_have_metadata_and_prompts() -> None:
    suites = list_benchmark_suites()
    ids = [suite.id for suite in suites]

    assert len(ids) == len(set(ids))
    for suite in suites:
        assert suite.description.strip()
        assert len(suite.prompts) >= 3
        assert len(suite.prompts) == len(set(suite.prompts))
        assert all(prompt.strip() for prompt in suite.prompts)


def test_unknown_benchmark_suite_error_lists_available_suites() -> None:
    with pytest.raises(ValueError) as exc_info:
        get_benchmark_suite("missing-suite")

    message = str(exc_info.value)
    assert "Unknown benchmark suite: missing-suite" in message
    for suite_id in EXPECTED_SUITES:
        assert suite_id in message


@pytest.mark.parametrize("suite_id", sorted(EXPECTED_SUITES))
def test_fake_adapter_can_run_each_benchmark_suite(suite_id: str) -> None:
    result = run_benchmark("fake:tts", suite=suite_id)

    assert result.suite == suite_id
    assert result.metrics["runs"] == len(get_benchmark_suite(suite_id).prompts)
    assert result.metrics["failures"] == 0
