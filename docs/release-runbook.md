# Release Runbook

This runbook is for maintainers preparing a public TimbreGrid alpha release. It assumes the release is cut from `main`.

## Preflight

1. Confirm the worktree is clean.
2. Confirm `pyproject.toml` has the intended version.
3. Add release notes under `docs/releases/<tag>.md`.
4. Run the local validation set:

```bash
uv sync --all-groups
uv run pytest
uv run timbregrid registry audit
uv run timbregrid registry build --check
for benchmark_dir in benchmarks/examples benchmarks/submissions; do
  for benchmark in "$benchmark_dir"/*.json; do
    test -e "$benchmark" || continue
    uv run timbregrid bench validate "$benchmark"
  done
done
```

5. Run a Docker smoke check when Docker is available:

```bash
docker build -t timbregrid:release-smoke .
docker run --rm -d --name timbregrid-release-smoke -p 8889:8889 timbregrid:release-smoke
curl -fsS http://127.0.0.1:8889/health
curl -fsS -o /tmp/timbregrid-release-smoke.wav \
  http://127.0.0.1:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"fake:tts","input":"Hello from release smoke","voice":"alloy","response_format":"wav"}'
docker stop timbregrid-release-smoke
```

## Publish

Create and push a tag:

```bash
git tag v0.1.0-alpha.N
git push origin v0.1.0-alpha.N
```

The release workflow builds Python artifacts, checks the registry, publishes the GHCR image, attaches release assets, and updates the hosted registry site.

If the tag already exists, use the manual `Release` workflow dispatch with the existing tag.

## Post-Release Checks

Verify:

- the GitHub release exists and includes `registry/index.json`, `docs/support-matrix.md`, wheel, and sdist assets;
- the hosted registry is reachable at `https://kiyeonjeon21.github.io/timbregrid/registry/index.json`;
- the GHCR package is public;
- the published image starts and serves deterministic fake audio.

Example image smoke:

```bash
docker pull ghcr.io/kiyeonjeon21/timbregrid:0.1.0-alpha.1
docker run --rm -d --name timbregrid-release-check -p 8891:8889 ghcr.io/kiyeonjeon21/timbregrid:0.1.0-alpha.1
curl -fsS http://127.0.0.1:8891/health
curl -fsS -o /tmp/timbregrid-release-check.wav \
  http://127.0.0.1:8891/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"fake:tts","input":"Hello from published image","voice":"alloy","response_format":"wav"}'
docker stop timbregrid-release-check
```

## Failure Handling

Do not overwrite or delete public artifacts unless the artifact is clearly broken and no users can reasonably depend on it. Prefer a follow-up prerelease tag with corrected artifacts and a short note in the previous release.

