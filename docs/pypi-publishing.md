# PyPI Publishing

TimbreGrid is published to PyPI as an alpha package. Future releases should continue to use PyPI Trusted Publishing through the manual `Publish PyPI` workflow.

Current public alpha:

```bash
uvx --from timbregrid==0.1.0a2 timbregrid --help
uvx --from timbregrid==0.1.0a2 timbregrid models list
uvx --from timbregrid==0.1.0a2 timbregrid doctor --help
```

The package metadata intentionally excludes the KittenTTS direct wheel dependency so the built wheel remains compatible with PyPI and standards-conformant package indexes.

References:

- PyPI Trusted Publishing: <https://docs.pypi.org/trusted-publishers/using-a-publisher/>
- Direct URL dependency limitation: <https://setuptools.pypa.io/en/stable/userguide/dependency_management.html#direct-url-dependencies>

## Future Release Flow

1. Create or reuse a release tag.
2. Confirm the built wheel metadata has no direct URL `Requires-Dist` entries.
3. Run the `Release` workflow first so GitHub release assets, GHCR, and hosted registry are already published.
4. Run the `Publish PyPI` workflow manually for the same tag.
5. Verify installation in a fresh environment, pinning the released version:

```bash
uvx --from timbregrid==<version> timbregrid models list
```

6. Smoke optional extras separately in clean environments. Kokoro is published as `timbregrid[kokoro]`; KittenTTS is installed explicitly from a source checkout as documented in [`kitten-tts.md`](kitten-tts.md).

The PyPI trusted publisher should stay configured as:

- repository: `kiyeonjeon21/timbregrid`;
- workflow: `publish-pypi.yml`;
- environment: `pypi`;
- project: `timbregrid`.

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
