# Benchmark Examples

This directory stores raw benchmark JSON artifacts that are safe to load in tests and routing examples.

The checked-in `fake:tts` artifact is deterministic and is not a hardware performance claim. It exists to document the wire format, exercise routing, and validate benchmark submission tooling.

Validate examples with:

```bash
uv run timbregrid bench validate benchmarks/examples/fake-tts.realtime-agent.json
```

Real submissions should include raw output from the benchmark CLI and a stable `hardware.profile` value such as `apple-silicon`, `cpu`, or `cuda`. Do not edit metrics by hand; validation recomputes aggregate metrics from the run entries.
