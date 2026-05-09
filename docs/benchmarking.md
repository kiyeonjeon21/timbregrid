# Benchmarking

TimbreGrid benchmarks produce raw JSON so latency, memory, failure rate, and hardware metadata can be reviewed without trusting a summary table.

Run a local benchmark:

```bash
uv run timbregrid bench fake:tts \
  --suite realtime-agent \
  --output /tmp/fake-tts.realtime-agent.json
```

Validate a benchmark JSON file before sharing it:

```bash
uv run timbregrid bench validate /tmp/fake-tts.realtime-agent.json
```

Available suites are `realtime-agent`, `narration`, `multilingual`, `cloning`, and `dialogue`.

Benchmark output should be treated as raw evidence, not a leaderboard result. Include the exact model id, suite, generated runs, aggregate metrics, Python version, OS, machine, processor, and any optional `hardware.profile` value used for routing comparisons.

The repository includes a deterministic fake example under `benchmarks/examples`. It is useful for schema and routing tests, but it is not an Apple Silicon, CPU, or CUDA performance claim.
