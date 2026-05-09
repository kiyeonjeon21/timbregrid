from pathlib import Path

import pytest

from timbregrid.manifest import ManifestError, load_manifest


def test_load_example_manifest() -> None:
    manifest = load_manifest(Path("manifests/fake-tts.yaml"))

    assert manifest.id == "fake:tts"
    assert manifest.audio.sample_rate_hz == 24000
    assert "wav" in manifest.audio.formats


def test_manifest_rejects_extra_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
schema_version: "0.1"
id: fake:bad
name: Bad
unknown: true
upstream: {homepage: https://example.com, license: mit, weights: none}
runtime: {kind: python}
capabilities: {}
audio: {sample_rate_hz: 24000, formats: [wav]}
voices: {}
policy: {}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ManifestError):
        load_manifest(path)
