# PyPI Publishing

TimbreGrid is prepared for its first PyPI alpha upload through the manual `Publish PyPI` workflow. The package metadata intentionally excludes the KittenTTS direct wheel dependency so the built wheel is compatible with PyPI and standards-conformant package indexes.

The project is not considered published to PyPI until a maintainer configures PyPI Trusted Publishing and runs the workflow for a release tag.

References:

- PyPI Trusted Publishing: <https://docs.pypi.org/trusted-publishers/using-a-publisher/>
- Direct URL dependency limitation: <https://setuptools.pypa.io/en/stable/userguide/dependency_management.html#direct-url-dependencies>

## Before First Upload

1. Confirm the built wheel metadata has no direct URL `Requires-Dist` entries.
2. Create a PyPI trusted publisher for:
   - repository: `kiyeonjeon21/timbregrid`;
   - workflow: `publish-pypi.yml`;
   - environment: `pypi`;
   - project: `timbregrid`.
3. Keep the GitHub `pypi` environment protected with manual approval.
4. Run the release workflow first so GitHub release assets, GHCR, and the hosted registry exist for the same tag.

## Publish Flow

1. Create or reuse a release tag.
2. Run the `Release` workflow first so GitHub release assets, GHCR, and hosted registry are already published.
3. Run the `Publish PyPI` workflow manually for the same tag.
4. Verify installation in a fresh environment:

```bash
uvx --from timbregrid timbregrid models list
```

5. Smoke optional extras separately in clean environments. Kokoro is published as `timbregrid[kokoro]`; KittenTTS is installed explicitly from a source checkout as documented in [`kitten-tts.md`](kitten-tts.md).

## Local Metadata Check

Before running the workflow, build the package and inspect the wheel metadata:

```bash
uv build --out-dir dist --clear
python - <<'PY'
from pathlib import Path
import zipfile

wheels = sorted(Path("dist").glob("*.whl"))
if len(wheels) != 1:
    raise SystemExit(f"expected exactly one wheel, found {len(wheels)}")

wheel = wheels[0]
with zipfile.ZipFile(wheel) as archive:
    metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
    metadata = archive.read(metadata_name).decode()

for line in metadata.splitlines():
    if line.startswith("Requires-Dist:") and " @ " in line:
        raise SystemExit(f"direct URL dependency in wheel metadata: {line}")
PY
```

## Policy

- Do not use long-lived PyPI API tokens for routine releases.
- Do not publish from a dirty local checkout.
- Do not add direct URL dependencies to published package metadata.
- Do not publish model weights or private voice assets as package data.
