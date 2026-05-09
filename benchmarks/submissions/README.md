# Benchmark Submissions

This directory stores raw benchmark JSON artifacts produced by contributors on real hardware.

Files in this directory are evidence for review and routing experiments, not general performance guarantees. Each file must be produced by `uv run timbregrid bench`, include `hardware.profile`, and pass:

```bash
uv run timbregrid bench validate benchmarks/submissions/<file>.json
```

The checked-in Kokoro artifact is a local Apple Silicon run for `kokoro:82m` on the `realtime-agent` suite. It should not be presented as a CPU, CUDA, or cross-machine performance claim.
