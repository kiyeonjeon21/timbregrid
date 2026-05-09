# TimbreGrid

TimbreGrid is an open compatibility and evaluation layer for open-source text-to-speech systems.

It provides model manifests, benchmark tooling, OpenAI-compatible speech conformance checks, benchmark-aware routing, and a small reference `/v1/audio/speech` gateway.

**Status**: early MVP. The fake gateway, manifest registry, benchmark CLI, conformance suite, benchmark validation, and optional Kokoro adapter are implemented. KittenTTS, Chatterbox, and Qwen3-TTS are currently manifest-only examples.

## Quickstart

Install dependencies with `uv`, then validate the built-in fake model manifest:

```bash
uv sync --all-groups
uv run timbregrid manifest validate manifests/fake-tts.yaml
```

Run a benchmark and validate the raw JSON output:

```bash
uv run timbregrid bench fake:tts \
  --suite realtime-agent \
  --hardware-profile generic-ci \
  --output /tmp/timbregrid-bench.json

uv run timbregrid bench validate /tmp/timbregrid-bench.json
```

Start the reference gateway:

```bash
uv run timbregrid serve --model fake:tts --port 8889
```

Call the OpenAI-compatible speech endpoint:

```bash
curl http://localhost:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"fake:tts","input":"Hello from TimbreGrid","voice":"alloy","response_format":"wav"}' \
  --output speech.wav
```

The fake adapter generates deterministic local audio bytes without downloading model weights. It is intended for schema, CLI, conformance, benchmark, routing, and SDK compatibility work.

## What Works Today

- Validate TimbreGrid model manifests from YAML, including link, license, runtime, format, and consent consistency.
- Generate a static registry index and support matrix from manifests.
- Run fake-adapter benchmark suites and write raw JSON output.
- Validate benchmark JSON examples and submissions for model ids, suites, hardware profiles, prompts, and aggregate metrics.
- Run OpenAI-compatible speech conformance checks.
- Serve `POST /v1/audio/speech` for `fake:tts`.
- Verify Python OpenAI SDK compatibility against the local gateway.
- Route `model="auto"` requests by benchmark data, manifest capabilities, response format, availability, and license policy.
- Run `kokoro:82m` when optional Kokoro dependencies and `espeak-ng` are installed.

Not included yet:

- KittenTTS, Chatterbox, or Qwen3-TTS inference adapters.
- SQLite voice metadata storage or provenance enforcement.
- Hosted registry publishing.
- SSE audio streaming.
- WebUI or third-party integration examples.

## Model Registry

Manifests live under [`manifests/`](manifests). Generated registry artifacts live at:

- [`registry/index.json`](registry/index.json)
- [`docs/support-matrix.md`](docs/support-matrix.md)

Regenerate and check them with:

```bash
uv run timbregrid registry build
uv run timbregrid registry build --check
```

Known model entries:

- `fake:tts`: deterministic test adapter.
- `kokoro:82m`: optional executable adapter via `timbregrid[kokoro]`.
- `kitten-tts:nano-0.8`: manifest-only edge/CPU example.
- `chatterbox:tts`: manifest-only expressive/cloning example.
- `qwen3-tts:0.6b-base`: manifest-only multilingual/cloning example.

## Benchmarks

Benchmark suites are defined for:

- `realtime-agent`
- `narration`
- `multilingual`
- `cloning`
- `dialogue`

Example:

```bash
uv run timbregrid bench fake:tts \
  --suite realtime-agent \
  --hardware-profile cpu \
  --output /tmp/fake.json
uv run timbregrid bench validate /tmp/fake.json
```

The checked-in benchmark under [`benchmarks/examples`](benchmarks/examples) is deterministic fake data. It documents the JSON format and supports tests; it is not a hardware performance claim.

Benchmark validation recomputes run counts, failures, failure rate, average latency metrics, peak memory, and suite prompts before accepting a submission.

See [`docs/benchmarking.md`](docs/benchmarking.md) and [`docs/benchmark-submissions.md`](docs/benchmark-submissions.md).

## Conformance Tests

Run conformance checks against any OpenAI-compatible TTS server:

```bash
uv run timbregrid conformance http://localhost:8889/v1 \
  --endpoint audio.speech \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output conformance.json
```

See [`docs/conformance.md`](docs/conformance.md).

## Routing

Explain how `model="auto"` is resolved:

```bash
uv run timbregrid route explain \
  --model auto \
  --voice alloy \
  --response-format wav \
  --purpose realtime \
  --license-policy commercial_ok \
  --target-latency-ms 350 \
  --hardware-profile generic-ci
```

If matching benchmark data is missing, routing falls back to manifest capabilities and model availability.

## Docker

Run the fake gateway container:

```bash
docker compose up --build
```

The Docker image is intentionally lightweight. It does not include Kokoro, `espeak-ng`, or PyTorch-class model dependencies.

## Optional Kokoro Adapter

Install optional Kokoro dependencies:

```bash
uv sync --extra kokoro
```

Kokoro may also require the system `espeak-ng` package. On macOS:

```bash
brew install espeak-ng
```

Try the adapter:

```bash
uv run timbregrid models inspect kokoro:82m
uv run timbregrid manifest validate manifests/kokoro-82m.yaml
uv run timbregrid bench kokoro:82m --suite realtime-agent --output /tmp/kokoro.json
uv run timbregrid serve --model kokoro:82m --port 8889
```

Use `response_format="wav"` and a Kokoro voice such as `af_heart`.

## Roadmap

Detailed phases and checklists live in [`docs/roadmap.md`](docs/roadmap.md). Public status is intentionally conservative:

| Phase | Status | Focus |
|---|---|---|
| Phase 0: Spec-first planning | complete | Manifest schema, speech models, benchmark suites, conformance cases, example manifests. |
| Phase 1: Useful OSS before runtime | partial | Manifest validation, benchmark CLI, conformance tooling, and submission validation work; real hardware benchmark artifacts still need contributors. |
| Phase 2: Reference gateway MVP | partial | Fake gateway, optional Kokoro adapter, Docker smoke path, and benchmark-aware routing work; KittenTTS and expressive/cloning adapters are next. |
| Phase 3: Community registry | partial | Local registry, generated support matrix, PR/issue templates, and CI checks exist; hosted registry, link/checksum validation, and install smoke coverage remain. |
| Phase 4: Voice governance and integrations | not started | Voice records, consent/provenance enforcement, `/v1/audio/voices`, and integration examples remain. |

Near-term next work:

- Publish real raw benchmark examples for Apple Silicon, CPU, and CUDA where available.
- Implement a KittenTTS adapter for edge/CPU use.
- Add local voice records, consent metadata, and `/v1/audio/voices`.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Manifest, benchmark, conformance, and adapter contributions are welcome.

Before opening a PR, run:

```bash
uv run pytest
uv run timbregrid registry build --check
for benchmark in benchmarks/examples/*.json; do uv run timbregrid bench validate "$benchmark"; done
```

## Security

Do not submit cloned voice samples, private datasets, API keys, or consent records to this repository. See [`SECURITY.md`](SECURITY.md).

## License

TimbreGrid core is licensed under the MIT License. See [`LICENSE`](LICENSE).

Upstream model code and weights keep their own licenses as listed in each model manifest.
