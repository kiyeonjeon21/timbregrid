# Adapter Contributions

Adapters make a manifest executable through the TimbreGrid gateway, benchmark CLI, routing layer, and conformance tests. Keep adapters small and optional unless they are lightweight enough for the default install.

## Requirements

- Do not add heavyweight model dependencies to the default dependency list.
- Put real model packages behind an optional extra, a documented source install path, or a container path.
- Keep import-time behavior cheap; model weights should load only when synthesis starts.
- Return `SpeechResult` with correct format, content type, duration, sample rate, and timing fields.
- Expose voices through `voices()` so `/v1/audio/voices` and synthesis validation stay consistent.
- Enforce custom/cloned voice provenance before treating cloning paths as production-ready.

## Implementation Checklist

1. Add or update the model manifest.
2. Add the adapter under `src/timbregrid/adapters/`.
3. Register it in `src/timbregrid/registry.py`.
4. Add focused tests that mock the upstream package when real model dependencies are unavailable.
5. Run the adapter with a real optional environment before adding benchmark claims.
6. Add raw benchmark JSON only from real runs produced by the CLI.

## Validation

Use the smallest set that covers the change:

```bash
uv run pytest
uv run timbregrid manifest validate manifests/<model>.yaml
uv run timbregrid registry audit
uv run timbregrid registry build
uv run timbregrid registry build --check
```

For real adapter smoke checks:

```bash
uv run timbregrid models inspect <model-id>
uv run timbregrid bench <model-id> --suite realtime-agent --hardware-profile <profile> --output <model>.json
uv run timbregrid bench validate <model>.json
uv run timbregrid serve --model <model-id> --port 8889
```

Only commit benchmark output when it is raw JSON from a reproducible run. Do not commit generated audio, downloaded weights, private voice records, or local cache paths.

