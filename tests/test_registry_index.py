import json
from pathlib import Path

from timbregrid.registry_index import (
    build_registry_artifacts,
    build_registry_index,
    stale_registry_artifacts,
    write_registry_artifacts,
)


def test_build_registry_index_uses_current_manifests() -> None:
    index = build_registry_index(Path("manifests"))

    assert index["schema_version"] == "0.1"
    assert index["model_count"] == 5
    assert [model["id"] for model in index["models"]] == [
        "chatterbox:tts",
        "fake:tts",
        "kitten-tts:nano-0.8",
        "kokoro:82m",
        "qwen3-tts:0.6b-base",
    ]


def test_registry_index_merges_static_runtime_status() -> None:
    index = build_registry_index(Path("manifests"))
    models = {model["id"]: model for model in index["models"]}

    assert models["fake:tts"]["available"] is True
    assert models["fake:tts"]["status"] == "available"
    assert models["kokoro:82m"]["available"] is False
    assert models["kokoro:82m"]["requires_extra"] == "kokoro"
    assert models["kokoro:82m"]["status"] == "requires optional dependency: kokoro"
    assert models["chatterbox:tts"]["available"] is False
    assert models["chatterbox:tts"]["executable"] is False
    assert models["chatterbox:tts"]["status"] == "manifest-only"


def test_registry_artifacts_are_deterministic() -> None:
    first = build_registry_artifacts(Path("manifests"))
    second = build_registry_artifacts(Path("manifests"))

    assert first == second
    body = json.loads(first.index_json)
    assert {model["id"] for model in body["models"]} >= {"fake:tts", "chatterbox:tts"}
    assert "| `fake:tts` |" in first.support_matrix_markdown


def test_write_and_check_registry_artifacts(tmp_path: Path) -> None:
    index_path = tmp_path / "registry" / "index.json"
    matrix_path = tmp_path / "docs" / "support-matrix.md"

    write_registry_artifacts(Path("manifests"), index_path, matrix_path)

    assert stale_registry_artifacts(Path("manifests"), index_path, matrix_path) == []

    matrix_path.write_text("stale\n", encoding="utf-8")

    assert stale_registry_artifacts(Path("manifests"), index_path, matrix_path) == [matrix_path]
