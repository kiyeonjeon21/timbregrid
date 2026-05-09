# Benchmarking

TimbreGrid benchmarks produce raw JSON so latency, memory, failure rate, and hardware metadata can be reviewed without trusting a summary table.

Run a local benchmark:

```bash
uv run timbregrid bench fake:tts \
  --suite realtime-agent \
  --hardware-profile cpu \
  --output /tmp/fake-tts.realtime-agent.json
```

Validate a benchmark JSON file before sharing it:

```bash
uv run timbregrid bench validate /tmp/fake-tts.realtime-agent.json
```

Available suites are `realtime-agent`, `narration`, `multilingual`, `cloning`, and `dialogue`.

Benchmark output should be treated as raw evidence, not a leaderboard result. Include the exact model id, suite, generated runs, aggregate metrics, Python version, OS, machine, processor, and `hardware.profile` value used for routing comparisons. If `--hardware-profile` is not provided, TimbreGrid infers `apple-silicon` on macOS ARM and `cpu` elsewhere; use explicit values such as `apple-silicon`, `cpu`, `cuda`, or `generic-ci` when comparing submissions.

The repository keeps deterministic fake examples under `benchmarks/examples` and real hardware submissions under `benchmarks/submissions`.

Fake examples are useful for schema and routing tests, but they are not Apple Silicon, CPU, or CUDA performance claims. Real submissions are raw contributor runs for review and comparison; they are not general performance guarantees across machines.
