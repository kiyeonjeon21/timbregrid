# Benchmark Submissions

Benchmark submissions should be raw JSON files produced by:

```bash
uv run timbregrid bench <model-id> --suite <suite-id> --output <file>.json
```

Before opening a PR, validate each file:

```bash
uv run timbregrid bench validate <file>.json
```

Submission checklist:

- Use a model id that exists in `manifests/*.yaml`.
- Use one of the defined benchmark suites.
- Include the complete raw JSON output, not a hand-written summary.
- Keep aggregate metrics consistent with the per-prompt `runs` entries.
- Include hardware metadata from the benchmark CLI. Add a stable `hardware.profile` such as `apple-silicon`, `cpu`, `cuda`, or a more specific project-approved profile when comparing routing behavior.
- Name files as `<model-id>.<suite-id>.<hardware-profile>.json`, replacing characters that are awkward in filenames with `-`.

Do not submit fabricated Apple Silicon, CPU, or CUDA results. If the run used the fake adapter or synthetic data, label it as an example and do not present it as hardware performance evidence.
