# PyPI Publishing

TimbreGrid is not published to PyPI yet. A manual `Publish PyPI` workflow is present so the release path is visible, but the current package metadata still contains a direct URL optional dependency for the official KittenTTS wheel. PyPI and standards-conformant package indexes do not accept published distributions that declare direct URL dependencies, so the workflow intentionally fails before upload until that is resolved.

References:

- PyPI Trusted Publishing: <https://docs.pypi.org/trusted-publishers/using-a-publisher/>
- Direct URL dependency limitation: <https://setuptools.pypa.io/en/stable/userguide/dependency_management.html#direct-url-dependencies>

## Before First Upload

1. Decide how to handle KittenTTS installation for PyPI users:
   - wait for an official index-hosted KittenTTS distribution and depend on that;
   - move the direct wheel install to documentation or a non-published development dependency group;
   - publish TimbreGrid without a `kitten` extra and keep KittenTTS source installs documented separately.
2. Remove direct URL dependencies from `[project.optional-dependencies]`.
3. Confirm the built wheel metadata has no direct URL `Requires-Dist` entries.
4. Create a PyPI trusted publisher for:
   - repository: `kiyeonjeon21/timbregrid`;
   - workflow: `publish-pypi.yml`;
   - environment: `pypi`;
   - project: `timbregrid`.
5. Keep the GitHub `pypi` environment protected with manual approval.

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

