import json
from pathlib import Path

from typer.testing import CliRunner

from timbregrid.cli import app


def test_manifest_validate_cli() -> None:
    result = CliRunner().invoke(app, ["manifest", "validate", "manifests/fake-tts.yaml"])

    assert result.exit_code == 0
    assert "OK" in result.stdout
    assert "fake:tts" in result.stdout


def test_bench_cli_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "bench.json"

    result = CliRunner().invoke(
        app,
        ["bench", "fake:tts", "--suite", "realtime-agent", "--output", str(output)],
    )

    assert result.exit_code == 0
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["model"] == "fake:tts"
    assert body["suite"] == "realtime-agent"
    assert body["metrics"]["runs"] == 3
    assert body["metrics"]["failures"] == 0
