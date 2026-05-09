# Benchmark Submissions

Benchmark submissions should be raw JSON files produced by:

```bash
uv run timbregrid bench <model-id> --suite <suite-id> --output <file>.json
```

Deterministic fake examples live in `benchmarks/examples`. Real hardware submissions live in `benchmarks/submissions` and should be treated as raw evidence from a specific contributor environment, not as broad performance guarantees.

Use `--hardware-profile <profile>` when the result should be compared for routing or documentation. Common profiles are `apple-silicon`, `cpu`, `cuda`, and `generic-ci`.

Prefer specific profiles when they make results easier to compare without overstating them:

- `apple-silicon`: contributor Apple Silicon runs where the exact chip is captured in `hardware`.
- `cpu`: general CPU-only runs when no more specific profile is agreed.
- `cuda`: CUDA runs where GPU details are captured in `hardware`.
- `generic-ci`: deterministic smoke data from CI or fake adapters.

Before opening a PR, validate each file:

```bash
uv run timbregrid bench validate <file>.json
```

Submission checklist:

- Use a model id that exists in `manifests/*.yaml`.
- Use one of the defined benchmark suites.
- Include the complete raw JSON output, not a hand-written summary.
- Keep aggregate metrics consistent with the per-prompt `runs` entries; validation recomputes run counts, failures, failure rate, averages, and peak memory.
- Include hardware metadata from the benchmark CLI with a stable `hardware.profile` such as `apple-silicon`, `cpu`, `cuda`, or a more specific project-approved profile.
- Name files as `<model-id>.<suite-id>.<hardware-profile>.json`, replacing characters that are awkward in filenames with `-`.

Example PR contents for a real benchmark submission:

- `benchmarks/submissions/kokoro-82m.realtime-agent.apple-silicon.json`
- a short PR note with OS, Python version, model install path, and whether the model was already cached;
- no generated audio, model weights, local cache paths, or private prompt data.

Do not submit fabricated Apple Silicon, CPU, or CUDA results. If the run used the fake adapter or synthetic data, label it as an example and do not present it as hardware performance evidence.
