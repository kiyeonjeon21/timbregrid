# TimbreGrid

[![CI](https://github.com/kiyeonjeon21/timbregrid/actions/workflows/ci.yml/badge.svg)](https://github.com/kiyeonjeon21/timbregrid/actions/workflows/ci.yml)

TimbreGrid is a local-first compatibility, evaluation, and routing layer for OpenAI-compatible open-source text-to-speech systems.

Open-source TTS has many promising models and servers, but comparing and integrating them is still awkward: every project has different install steps, voice names, audio formats, runtime assumptions, and benchmark claims. TimbreGrid makes those pieces explicit through manifests, raw benchmark JSON, conformance checks, diagnostic reports, routing policy, and a small reference `/v1/audio/speech` gateway.

**Status**: early MVP. The fake gateway, manifest registry, diagnostic CLI, benchmark CLI, conformance suite, benchmark validation, optional Kokoro adapter, and optional KittenTTS adapter are implemented. Chatterbox and Qwen3-TTS are currently manifest-only examples.

Use TimbreGrid when you want to:

- diagnose whether an OpenAI-compatible TTS server behaves well enough for basic `/v1/audio/speech` usage;
- run a local OSS TTS model behind a reference OpenAI-compatible speech endpoint;
- compare adapters with reviewable raw benchmark output instead of hand-written summary tables;
- describe model capabilities, licenses, voices, formats, and runtime requirements in validated manifests;
- test another TTS server's basic OpenAI-compatible speech behavior;
- route `model="auto"` requests by benchmark evidence, manifest capabilities, response format, availability, and license policy;
- keep local/custom voice provenance and consent metadata explicit before cloning workflows become first-class.

## Current Value

| Area | What works now |
|---|---|
| Diagnostics | `timbregrid doctor` produces a compatibility report for any OpenAI-compatible `/v1/audio/speech` server. |
| Runtime | `fake:tts`, optional `kokoro:82m`, and optional `kitten-tts:nano-0.8` can serve `POST /v1/audio/speech`. |
| Evaluation | Benchmark suites emit raw JSON and validation recomputes counts, failures, latency averages, memory, and prompt coverage. |
| Compatibility | Basic OpenAI-compatible speech conformance checks and Python OpenAI SDK compatibility tests are included. |
| Registry | YAML manifests generate `registry/index.json`, the support matrix, release assets, and a hosted latest registry. |
| Routing | `model="auto"` can choose from available models using benchmark data and manifest policy. |
| Voice governance | Builtin and local voices are discoverable through `GET /v1/audio/voices`; local/custom voices require consent and provenance metadata. |

## Quickstart

Try the compatibility stack without downloading model weights. The built-in fake adapter is deterministic and exists so manifests, benchmarks, conformance, routing, Docker, and SDK compatibility can be tested quickly.

Run the published alpha container:

```bash
docker run --rm -p 8889:8889 ghcr.io/kiyeonjeon21/timbregrid:0.1.0-alpha.1
```

Then call the OpenAI-compatible speech endpoint:

```bash
curl http://localhost:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"fake:tts","input":"Hello from TimbreGrid","voice":"alloy","response_format":"wav"}' \
  --output speech.wav
```

The generated `speech.wav` is test audio, not natural speech. Install the optional Kokoro or KittenTTS adapters below when you want real local synthesis.

For a real voice demo, see [`docs/real-audio-demo.md`](docs/real-audio-demo.md).

## Run From Source

Install dependencies with `uv`, then validate the built-in model manifest:

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

Start the reference gateway from source:

```bash
uv run timbregrid serve --model fake:tts --port 8889
```

Call the same speech endpoint:

```bash
curl http://localhost:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"fake:tts","input":"Hello from TimbreGrid","voice":"alloy","response_format":"wav"}' \
  --output speech.wav
```

## What Works Today

- Validate TimbreGrid model manifests from YAML, including link, license, runtime, format, and consent consistency.
- Generate a static registry index and support matrix from manifests.
- Run fake-adapter benchmark suites and write raw JSON output.
- Validate benchmark JSON examples and submissions for model ids, suites, hardware profiles, prompts, and aggregate metrics.
- Produce a basic compatibility diagnosis for an OpenAI-compatible TTS server with `timbregrid doctor`.
- Run basic OpenAI-compatible speech conformance checks.
- Serve `POST /v1/audio/speech` for `fake:tts`.
- Expose builtin and local voice metadata through `GET /v1/audio/voices` and enforce known voice metadata during synthesis.
- Verify Python OpenAI SDK compatibility and run a direct SDK example against the local gateway.
- Route `model="auto"` requests by benchmark data, manifest capabilities, response format, availability, and license policy.
- Run `kokoro:82m` when optional Kokoro dependencies and `espeak-ng` are installed.
- Run `kitten-tts:nano-0.8` when optional KittenTTS dependencies are installed.

Not included yet:

- Chatterbox or Qwen3-TTS inference adapters.
- SQLite voice metadata storage or custom voice synthesis.
- PyPI publishing. A manual workflow and runbook exist, but package metadata still needs a PyPI-compatible KittenTTS install path.
- SSE audio streaming.
- Pipecat or LiveKit integration examples; Open WebUI is currently a docs-only TTS guide.

## Model Registry

Manifests live under [`manifests/`](manifests). Generated registry artifacts live at:

- [`registry/index.json`](registry/index.json)
- [`docs/support-matrix.md`](docs/support-matrix.md)

The latest published registry is hosted at:

- <https://kiyeonjeon21.github.io/timbregrid/registry/index.json>

Versioned registry artifacts are also attached to GitHub releases.

Regenerate and check them with:

```bash
uv run timbregrid registry build
uv run timbregrid registry build --check
uv run timbregrid registry audit --skip-network
```

Required PR checks use `--skip-network` so external GitHub or Hugging Face outages do not block unrelated changes. Release and scheduled registry checks run the full URL audit.

Known model entries:

- `fake:tts`: deterministic test adapter.
- `kokoro:82m`: optional executable adapter via `timbregrid[kokoro]`.
- `kitten-tts:nano-0.8`: optional executable edge/CPU adapter via `timbregrid[kitten]`.
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

Raw real-hardware submissions live under [`benchmarks/submissions`](benchmarks/submissions). The checked-in Kokoro and KittenTTS Apple Silicon artifacts are contributor machine runs, not general performance guarantees.

Benchmark validation recomputes run counts, failures, failure rate, average latency metrics, peak memory, and suite prompts before accepting a submission.

See [`docs/benchmarking.md`](docs/benchmarking.md) and [`docs/benchmark-submissions.md`](docs/benchmark-submissions.md).

## Examples

Run the OpenAI Python SDK example against a local gateway:

```bash
uv run python examples/openai_sdk_speech.py
```

For KittenTTS:

```bash
TIMBREGRID_MODEL=kitten-tts:nano-0.8 \
TIMBREGRID_VOICE=Jasper \
TIMBREGRID_OUTPUT=/tmp/kitten-sdk.wav \
uv run python examples/openai_sdk_speech.py
```

For Kokoro:

```bash
TIMBREGRID_MODEL=kokoro:82m \
TIMBREGRID_VOICE=af_heart \
TIMBREGRID_OUTPUT=/tmp/kokoro-sdk.wav \
uv run python examples/openai_sdk_speech.py
```

## Doctor And Conformance

For a user-facing diagnosis of a TTS server, run:

```bash
uv run timbregrid doctor http://localhost:8889/v1 \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output doctor.json
```

The doctor command wraps conformance results into a compatibility report for basic Open WebUI-style and Pipecat OpenAI TTS-style readiness. It is not a full integration certification.

Run conformance checks against any OpenAI-compatible TTS server:

```bash
uv run timbregrid conformance http://localhost:8889/v1 \
  --endpoint audio.speech \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output conformance.json
```

See [`docs/doctor.md`](docs/doctor.md) and [`docs/conformance.md`](docs/conformance.md).

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

## Voice Metadata

List builtin voices and local voice records:

```bash
curl "http://localhost:8889/v1/audio/voices?model=fake:tts"
```

Local voice records can be supplied as JSON without committing private assets:

```bash
TIMBREGRID_VOICE_CATALOG=/path/to/voices.json uv run timbregrid serve
```

Speech requests must use a known builtin voice or a local catalog voice for the selected model. Custom or local voices must set `builtin=false`, set `source` to `local` or `custom`, include `consent="granted"`, and provide a non-empty `provenance` value. TimbreGrid exposes these records for governance and discovery; it does not synthesize cloned voices yet.

## Optional KittenTTS Adapter

Install optional KittenTTS dependencies while keeping development dependencies available:

```bash
uv sync --all-groups --extra kitten
```

To keep Kokoro installed in the same environment, include both extras in the same sync:

```bash
uv sync --all-groups --extra kitten --extra kokoro
```

Try the adapter:

```bash
uv run timbregrid models inspect kitten-tts:nano-0.8
uv run timbregrid manifest validate manifests/kitten-tts-nano-0.8.yaml
uv run timbregrid serve --model kitten-tts:nano-0.8 --port 8889
```

Use `response_format="wav"` or `response_format="pcm"` and a KittenTTS voice such as `Jasper`.

## Integrations

TimbreGrid can be used as a local OpenAI-compatible TTS backend for tools that call `/v1/audio/speech`.

- [Open WebUI integration guide](docs/integrations/open-webui.md)

Integration examples are intentionally narrow until streaming and broader gateway compatibility stabilize.

## Release Status

The alpha release path publishes GitHub release assets, a hosted registry, and a lightweight GHCR image. Maintainer notes live in [`docs/release-runbook.md`](docs/release-runbook.md). PyPI publishing is tracked separately in [`docs/pypi-publishing.md`](docs/pypi-publishing.md) because the current KittenTTS install path uses a direct wheel URL that is not valid for PyPI package metadata.

## Docker

Run the published alpha image:

```bash
docker run --rm -p 8889:8889 ghcr.io/kiyeonjeon21/timbregrid:0.1.0-alpha.1
```

Or build the fake gateway container locally:

```bash
docker compose up --build
```

The Docker image is intentionally lightweight. It does not include Kokoro, `espeak-ng`, or PyTorch-class model dependencies.

## Optional Kokoro Adapter

Install optional Kokoro dependencies:

```bash
uv sync --all-groups --extra kokoro
```

Kokoro may also require the system `espeak-ng` package. On macOS:

```bash
brew install espeak-ng
```

Try the adapter:

```bash
uv run timbregrid models inspect kokoro:82m
uv run timbregrid manifest validate manifests/kokoro-82m.yaml
uv run timbregrid bench kokoro:82m \
  --suite realtime-agent \
  --hardware-profile cpu \
  --output /tmp/kokoro.json
uv run timbregrid serve --model kokoro:82m --port 8889
```

Use `response_format="wav"` and a Kokoro voice such as `af_heart`.

## Roadmap

Detailed phases and checklists live in [`docs/roadmap.md`](docs/roadmap.md). Public status is intentionally conservative:

| Phase | Status | Focus |
|---|---|---|
| Phase 0: Spec-first planning | complete | Manifest schema, speech models, benchmark suites, conformance cases, example manifests. |
| Phase 1: Useful OSS before runtime | partial | Manifest validation, benchmark CLI, conformance tooling, submission validation, and Kokoro/KittenTTS Apple Silicon artifacts exist; broader hardware coverage still needs contributors. |
| Phase 2: Reference gateway MVP | partial | Fake gateway, optional Kokoro and KittenTTS adapters, Docker smoke path, and benchmark-aware routing work; expressive/cloning adapters are next. |
| Phase 3: Community registry | partial | Local registry, generated support matrix, release assets, hosted latest registry, PR/issue templates, deterministic registry audit, scheduled URL audit, and CI checks exist; checksum validation and broader install smoke coverage remain. |
| Phase 4: Voice governance and integrations | partial | Local voice records, consent/provenance metadata, `/v1/audio/voices`, synthesis-time voice checks, a real-audio demo guide, and Open WebUI docs exist; Pipecat and LiveKit examples remain. |

Near-term next work:

- Collect more real raw benchmark examples for CPU, CUDA, and additional Apple Silicon environments.
- Use `timbregrid doctor` reports to harden Open WebUI, Pipecat, and LiveKit integration examples.
- Implement an expressive or cloning adapter, likely Chatterbox first.
- Harden checksum metadata, optional install smoke coverage, and PyPI publishing readiness.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Manifest, benchmark, conformance, and adapter contributions are welcome.

Focused contribution guides:

- [`docs/manifest-contributions.md`](docs/manifest-contributions.md)
- [`docs/benchmark-submissions.md`](docs/benchmark-submissions.md)
- [`docs/adapter-contributions.md`](docs/adapter-contributions.md)

Before opening a PR, run:

```bash
uv run pytest
uv run timbregrid registry audit --skip-network
uv run timbregrid registry build --check
for benchmark in benchmarks/examples/*.json; do uv run timbregrid bench validate "$benchmark"; done
for benchmark in benchmarks/submissions/*.json; do uv run timbregrid bench validate "$benchmark"; done
```

## Security

Do not submit cloned voice samples, private datasets, API keys, or consent records to this repository. See [`SECURITY.md`](SECURITY.md).

## License

TimbreGrid core is licensed under the MIT License. See [`LICENSE`](LICENSE).

Upstream model code and weights keep their own licenses as listed in each model manifest.
