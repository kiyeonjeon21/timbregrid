from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import httpx

from timbregrid.manifest import ManifestError, load_manifest
from timbregrid.models import ModelManifest


KNOWN_LICENSE_IDENTIFIERS = frozenset(
    {
        "agpl-3.0-only",
        "agpl-3.0-or-later",
        "apache-2.0",
        "bsd-2-clause",
        "bsd-3-clause",
        "cc-by-4.0",
        "cc-by-nc-4.0",
        "cc-by-nc-sa-4.0",
        "cc-by-sa-4.0",
        "cc0-1.0",
        "gpl-3.0-only",
        "gpl-3.0-or-later",
        "isc",
        "lgpl-3.0-only",
        "lgpl-3.0-or-later",
        "mit",
        "mpl-2.0",
    }
)


@dataclass(frozen=True)
class RegistryAuditIssue:
    path: Path
    model_id: str | None
    field: str
    message: str

    def format(self) -> str:
        model = f" ({self.model_id})" if self.model_id else ""
        return f"{self.path}{model}: {self.field}: {self.message}"


@dataclass(frozen=True)
class RegistryAuditReport:
    manifest_count: int
    url_count: int
    issues: list[RegistryAuditIssue]

    @property
    def ok(self) -> bool:
        return not self.issues


def audit_registry(
    manifest_dir: Path,
    *,
    check_urls: bool = True,
    timeout: float = 5.0,
    url_checker: Callable[[str, float], str | None] | None = None,
) -> RegistryAuditReport:
    manifest_paths = sorted(manifest_dir.glob("*.yaml"))
    if not manifest_paths:
        return RegistryAuditReport(
            manifest_count=0,
            url_count=0,
            issues=[
                RegistryAuditIssue(
                    path=manifest_dir,
                    model_id=None,
                    field="manifest_dir",
                    message="no manifests found",
                )
            ],
        )

    checker = url_checker or check_url_reachable
    issues: list[RegistryAuditIssue] = []
    url_count = 0

    for path in manifest_paths:
        try:
            manifest = load_manifest(path)
        except ManifestError as exc:
            issues.append(
                RegistryAuditIssue(
                    path=path,
                    model_id=None,
                    field="manifest",
                    message=str(exc),
                )
            )
            continue

        if manifest.upstream.license not in KNOWN_LICENSE_IDENTIFIERS:
            issues.append(
                RegistryAuditIssue(
                    path=path,
                    model_id=manifest.id,
                    field="upstream.license",
                    message=f"unknown license identifier: {manifest.upstream.license}",
                )
            )

        if not check_urls:
            continue

        for field, url in _upstream_urls(manifest):
            url_count += 1
            error = checker(url, timeout)
            if error:
                issues.append(
                    RegistryAuditIssue(
                        path=path,
                        model_id=manifest.id,
                        field=field,
                        message=f"unreachable URL: {url} ({error})",
                    )
                )

    return RegistryAuditReport(
        manifest_count=len(manifest_paths),
        url_count=url_count,
        issues=issues,
    )


def check_url_reachable(url: str, timeout: float = 5.0) -> str | None:
    headers = {"User-Agent": "timbregrid-registry-audit/0.1"}
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout, headers=headers) as client:
            response = client.head(url)
            if response.status_code < 400:
                return None
            if response.status_code in {403, 405}:
                response = client.get(url)
                if response.status_code < 400:
                    return None
            return f"HTTP {response.status_code}"
    except httpx.HTTPError as exc:
        return exc.__class__.__name__


def _upstream_urls(manifest: ModelManifest) -> list[tuple[str, str]]:
    urls = [("upstream.homepage", manifest.upstream.homepage)]
    if _is_http_url(manifest.upstream.weights):
        urls.append(("upstream.weights", manifest.upstream.weights))
    return urls


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
