from pathlib import Path

from timbregrid.registry_audit import audit_registry


def test_registry_audit_accepts_current_manifests_without_network() -> None:
    report = audit_registry(Path("manifests"), check_urls=False)

    assert report.ok
    assert report.manifest_count == 5
    assert report.url_count == 0


def test_registry_audit_rejects_unknown_license(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    (manifest_dir / "bad.yaml").write_text(
        _manifest(license_id="made-up-license"),
        encoding="utf-8",
    )

    report = audit_registry(manifest_dir, check_urls=False)

    assert not report.ok
    assert report.issues[0].field == "upstream.license"
    assert "made-up-license" in report.issues[0].message


def test_registry_audit_reports_url_failures(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    (manifest_dir / "test.yaml").write_text(_manifest(), encoding="utf-8")

    report = audit_registry(
        manifest_dir,
        url_checker=lambda _url, _timeout: "HTTP 404",
    )

    assert not report.ok
    assert report.url_count == 1
    assert report.issues[0].field == "upstream.homepage"
    assert "HTTP 404" in report.issues[0].message


def test_registry_audit_reports_empty_manifest_directory(tmp_path: Path) -> None:
    report = audit_registry(tmp_path, check_urls=False)

    assert not report.ok
    assert report.issues[0].field == "manifest_dir"


def _manifest(*, license_id: str = "mit") -> str:
    return f"""
schema_version: "0.1"
id: fake:test
name: Test TTS
upstream:
  homepage: https://example.com/model
  license: {license_id}
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
""".strip()
