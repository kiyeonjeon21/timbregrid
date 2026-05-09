# PyPI Publishing

TimbreGrid is not published to PyPI yet. A manual `Publish PyPI` workflow is present so the release path is visible, but the current package metadata still contains a direct URL optional dependency for the official KittenTTS wheel. PyPI and standards-conformant package indexes do not accept published distributions that declare direct URL dependencies, so the workflow intentionally fails before upload until that is resolved.

References:

- PyPI Trusted Publishing: <https://docs.pypi.org/trusted-publishers/using-a-publisher/>
- Direct URL dependency limitation: <https://setuptools.pypa.io/en/stable/userguide/dependency_management.html#direct-url-dependencies>

## Before First Upload

Current default: keep the working KittenTTS source install path and do not publish to PyPI until the dependency metadata is compatible with package indexes.

Before the first PyPI upload, choose one KittenTTS packaging strategy:

1. Wait for an official index-hosted KittenTTS distribution and depend on that.
2. Move the direct wheel install to documentation or a non-published development dependency group.
3. Publish TimbreGrid without a `kitten` extra and keep KittenTTS source installs documented separately.

Then:

1. Remove direct URL dependencies from `[project.optional-dependencies]`.
2. Confirm the built wheel metadata has no direct URL `Requires-Dist` entries.
3. Create a PyPI trusted publisher for:
   - repository: `kiyeonjeon21/timbregrid`;
   - workflow: `publish-pypi.yml`;
   - environment: `pypi`;
   - project: `timbregrid`.
4. Keep the GitHub `pypi` environment protected with manual approval.
5. Remove the guard in `publish-pypi.yml` only after the metadata blocker is gone.

## Publish Flow

After the metadata blocker is resolved:

1. Create or reuse a release tag.
2. Run the `Release` workflow first so GitHub release assets, GHCR, and hosted registry are already published.
3. Run the `Publish PyPI` workflow manually for the same tag.
4. Verify installation in a fresh environment:

```bash
uvx --from timbregrid timbregrid models list
```

5. If optional extras are available, smoke them separately in clean environments.

## Policy

- Do not use long-lived PyPI API tokens for routine releases.
- Do not publish from a dirty local checkout.
- Do not add direct URL dependencies to published package metadata.
- Do not publish model weights or private voice assets as package data.
