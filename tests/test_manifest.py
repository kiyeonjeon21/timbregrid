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


def test_manifest_rejects_invalid_homepage(tmp_path: Path) -> None:
    path = _write_manifest(tmp_path, _valid_manifest().replace("https://example.com/model", "not-a-url"))

    with pytest.raises(ManifestError, match="upstream.homepage"):
        load_manifest(path)


def test_manifest_requires_python_package(tmp_path: Path) -> None:
    path = _write_manifest(
        tmp_path,
        _valid_manifest().replace("  package: example-tts\n", ""),
    )

    with pytest.raises(ManifestError, match="runtime.package"):
        load_manifest(path)


def test_manifest_rejects_format_mismatch(tmp_path: Path) -> None:
    path = _write_manifest(
        tmp_path,
        _valid_manifest().replace("  formats: [wav]\nvoices:", "  formats: [pcm]\nvoices:"),
    )

    with pytest.raises(ManifestError, match="formats must match"):
        load_manifest(path)


def test_manifest_rejects_cloning_without_consent(tmp_path: Path) -> None:
    manifest = _valid_manifest().replace("  voice_cloning: false", "  voice_cloning: true")
    manifest = manifest.replace("  builtin: true\n  custom: false", "  builtin: false\n  custom: true")
    path = _write_manifest(tmp_path, manifest)

    with pytest.raises(ManifestError, match="requires_voice_consent"):
        load_manifest(path)


def _write_manifest(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "manifest.yaml"
    path.write_text(body.strip(), encoding="utf-8")
    return path


def _valid_manifest() -> str:
    return """
schema_version: "0.1"
id: fake:test
name: Test TTS
upstream:
  homepage: https://example.com/model
  license: mit
  weights: none
runtime:
  kind: python
  package: example-tts
  acceleration:
    cpu: true
capabilities:
  streaming: false
  voice_cloning: false
  multilingual: none
  long_form: limited
  formats: [wav]
audio:
  sample_rate_hz: 24000
  formats: [wav]
voices:
  builtin: true
  custom: false
policy:
  commercial_use: true
  requires_voice_consent: false
"""
