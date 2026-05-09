# Contributing

TimbreGrid is early, so contributions should keep the default install lightweight and the validation path clear.

## Good First Contributions

- Improve model manifests under `manifests/`.
- Add benchmark JSON examples produced by `uv run timbregrid bench`.
- Improve conformance coverage for OpenAI-compatible TTS servers.
- Add optional adapters without adding heavyweight dependencies to the default install.
- Improve documentation and setup reliability.

## Issues

Use the issue templates for bug reports, feature requests, model manifest requests, and benchmark submissions. Security issues should follow `SECURITY.md` and should not include sensitive details in public issues.

## Development Setup

```bash
uv sync --all-groups
uv run pytest
```

## Validation Checklist

Run the checks that match your change:

```bash
uv run pytest
uv run timbregrid registry audit --skip-network
uv run timbregrid registry build --check
for benchmark in benchmarks/examples/*.json; do uv run timbregrid bench validate "$benchmark"; done
for benchmark in benchmarks/submissions/*.json; do uv run timbregrid bench validate "$benchmark"; done
```

For manifest changes:

```bash
uv run timbregrid manifest validate manifests/<model>.yaml
uv run timbregrid registry audit --skip-network
uv run timbregrid registry build
uv run timbregrid registry build --check
```

Maintainer release and scheduled checks run the full network audit with `uv run timbregrid registry audit --timeout 5`.

For benchmark submissions:

```bash
uv run timbregrid bench validate <file>.json
```

## Model Manifests

Every manifest should include:

- upstream homepage and license;
- model weights location or clear weights status;
- runtime package and acceleration requirements;
- audio formats and sample rate;
- voice, cloning, multilingual, long-form, streaming, and style-control capability flags;
- policy notes for commercial use and consent requirements.

Do not mark a model executable unless this repo includes an adapter or an explicit optional extra for it.

Manifest validation also checks URL shape, lowercase SPDX-style license identifiers, runtime package presence for Python runtimes, matching audio/capability formats, and consent requirements for custom or cloning voices.

See `docs/manifest-contributions.md` for the full manifest PR flow.

## Adapter Contributions

Adapters should keep heavyweight model dependencies optional, load model packages lazily, expose voices through the registry, and include tests that do not require downloading large weights.

See `docs/adapter-contributions.md` for the adapter checklist.

## Benchmark Data

Submit raw JSON produced by the benchmark CLI. Do not hand-write metrics or submit fabricated hardware results.

Fake or synthetic examples are acceptable only when clearly labeled as examples.

## Voice And Consent Data

Do not submit private voice samples, cloned voice references, consent records, private datasets, or personal identifiers.
