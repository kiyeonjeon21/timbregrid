# Model Manifest Contributions

Model manifests are the lowest-friction way to improve TimbreGrid. A good manifest makes a model's source, license, runtime requirements, audio formats, voice behavior, and safety caveats reviewable before an adapter exists.

## Scope

Add or update a manifest when you can provide stable public metadata for a model. Do not mark a model executable unless TimbreGrid already has an adapter path for it.

Required evidence:

- upstream homepage;
- SPDX-style license identifier already accepted by `timbregrid registry audit`;
- weights URL, `open-weight`, or `none`;
- runtime package name and acceleration targets;
- supported audio formats and sample rate;
- builtin/custom voice support;
- commercial-use and voice-consent policy notes.

## Workflow

1. Add `manifests/<model-id>.yaml`.
2. Run semantic validation:

```bash
uv run timbregrid manifest validate manifests/<model-id>.yaml
```

3. Run registry metadata audit:

```bash
uv run timbregrid registry audit --skip-network
```

Required PR checks skip network access so external outages do not block unrelated changes. Maintainer release and scheduled checks run the full URL audit with `uv run timbregrid registry audit --timeout 5`.

4. Regenerate registry artifacts:

```bash
uv run timbregrid registry build
uv run timbregrid registry build --check
```

5. Include the generated `registry/index.json` and `docs/support-matrix.md` changes in the PR.

## Review Notes

- `upstream.license` must be lowercase and in the audit allow-list. If a model uses a valid license that is not listed yet, update the allow-list and explain the source.
- `upstream.homepage` and URL weights must be public, stable links.
- `capabilities.formats` and `audio.formats` must match.
- Voice cloning or custom voices must set `policy.requires_voice_consent=true`.
- Do not submit private datasets, reference voice samples, consent records, API keys, or local filesystem paths.
