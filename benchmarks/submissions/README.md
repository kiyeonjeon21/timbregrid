# Benchmark Submissions

This directory stores raw benchmark JSON artifacts produced by contributors on real hardware.

Files in this directory are evidence for review and routing experiments, not general performance guarantees. Each file must be produced by `uv run timbregrid bench`, include `hardware.profile`, and pass:

```bash
uv run timbregrid bench validate benchmarks/submissions/<file>.json
```

The checked-in Kokoro and KittenTTS artifacts are local Apple Silicon runs on the `realtime-agent` suite. They should not be presented as CPU, CUDA, or cross-machine performance claims.
