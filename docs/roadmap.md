# TimbreGrid Roadmap

This document keeps the detailed implementation roadmap out of the public README while preserving the phase structure used to drive development.

The roadmap is directional, not a release commitment. Priorities may change as adapter feasibility, contributor interest, benchmark evidence, and safety requirements become clearer.

Roadmap status is conservative: an item is complete only when the implementation and relevant validation have both landed. Manifest-only models, deterministic fake benchmark data, and optional adapters are labeled as such.

## Phase 0: Spec-First Planning

- [x] Define the TimbreGrid model manifest schema.
- [x] Define `SpeechRequest`, `SpeechResult`, `Capabilities`, and `VoiceInfo`.
- [x] Define benchmark prompt suites: `realtime-agent`, `narration`, `multilingual`, `cloning`, and `dialogue`.
- [x] Define OpenAI-compatible speech conformance cases.
- [x] Create example manifests for Kokoro, KittenTTS, Chatterbox, and Qwen3-TTS.

## Phase 1: Useful OSS Before Runtime

- [x] Add `timbregrid manifest validate`.
- [x] Add semantic manifest validation for URLs, licenses, runtime package metadata, audio formats, and consent consistency.
- [x] Add `timbregrid bench` against a local adapter.
- [x] Add benchmark submission validation for model ids, suites, hardware profiles, prompts, run fields, and aggregate metrics.
- [x] Add `timbregrid conformance` for existing OpenAI-compatible TTS servers.
- [x] Document how other servers can use the benchmark and conformance tests.
- [ ] Publish real raw benchmark JSON examples for Apple Silicon, CPU, and CUDA where available.
  - Partial: deterministic fake benchmark examples, validation paths, and one Kokoro Apple Silicon submission exist.
  - Completion requires broader raw benchmark JSON produced on real hardware, not fabricated or hand-edited summaries.

## Phase 2: Reference Gateway MVP

- [x] Add a `POST /v1/audio/speech` compatible endpoint.
- [x] Add the deterministic `fake:tts` adapter for schema, gateway, routing, SDK, conformance, and benchmark development.
- [x] Add Kokoro as the first optional real-model baseline through `timbregrid[kokoro]`.
- [x] Add `model="auto"` routing by benchmark data, manifest capabilities, response format, availability, purpose, hardware profile, and license policy.
- [x] Add a lightweight Docker smoke path for the fake gateway.
- [ ] Implement a KittenTTS adapter for the edge/CPU lane.
- [ ] Implement one expressive or cloning backend, likely Chatterbox first.
- [ ] Add SSE audio streaming after the non-streaming gateway contract is stable.

## Phase 3: Community Registry

- [x] Generate a local static registry index from manifests.
- [x] Generate the model support matrix from manifests.
- [x] Add benchmark result submission docs and validation.
- [x] Add PR and issue templates for manifests, benchmarks, bugs, and features.
- [x] Run CI checks for tests, manifest validation, registry drift, benchmark examples, benchmark smoke, Docker smoke, and conformance against the Docker gateway.
- [ ] Publish a hosted static registry index.
- [ ] Add stronger deterministic CI checks for upstream links, checksums, license identifiers, and optional install smoke tests.
- [ ] Add a clearer external manifest contribution guide once the first outside-style manifest PR flow is tested.

## Phase 4: Voice Governance And Integrations

- [x] Add local voice records.
- [x] Add consent metadata and provenance fields for custom/cloned voices.
- [x] Add `GET /v1/audio/voices`.
- [ ] Add consent/provenance enforcement hooks before cloning adapters are treated as production-ready.
- [x] Add a direct OpenAI SDK usage example beyond compatibility tests.
- [ ] Add integration examples for Open WebUI, Pipecat, and LiveKit.
- [ ] Add a WebUI for A/B tests, latency views, and voice preview only after the CLI/gateway contracts stabilize.

## First Milestone

The first public milestone should stay small, testable, and useful outside this repo:

```bash
uv sync --all-groups --extra kokoro
uv run timbregrid models inspect kokoro:82m
uv run timbregrid manifest validate manifests/kokoro-82m.yaml
uv run timbregrid bench kokoro:82m \
  --suite realtime-agent \
  --hardware-profile cpu \
  --output kokoro.json
uv run timbregrid serve --model kokoro:82m --port 8889
uv run timbregrid conformance http://localhost:8889/v1 \
  --endpoint audio.speech \
  --model kokoro:82m \
  --voice af_heart \
  --response-format wav \
  --output kokoro-conformance.json
```

Success means:

- an existing OpenAI SDK client can generate audio locally;
- the model has a reviewable manifest;
- the benchmark output is reproducible and validates;
- another TTS server can run the same conformance tests;
- the project has value before adding several more model backends.

## Next Milestones

1. **Real benchmark artifacts**: collect raw benchmark JSON for Kokoro and future adapters on CPU, CUDA, and additional Apple Silicon environments where contributors can provide real runs.
2. **KittenTTS edge adapter**: add the first lightweight CPU-focused adapter without adding heavy dependencies to the default install path.
3. **Voice governance enforcement**: add synthesis-time consent/provenance checks before treating cloning adapters as a mainline feature.
4. **Integration examples**: add Open WebUI, Pipecat, and LiveKit docs or examples after the direct OpenAI SDK example.

## Technical Choices

- **Core language**: Python first, because model wrappers and audio tooling are Python-heavy.
- **Gateway**: FastAPI, with ASGI streaming only after non-streaming compatibility is stable.
- **Manifest format**: YAML for authoring; Pydantic models and generated registry artifacts for validation and publishing.
- **Storage**: SQLite is planned for model, voice, and benchmark metadata; the current MVP uses filesystem artifacts.
- **Runtime isolation**: in-process for small adapters; optional extras or sidecar/container paths for PyTorch-heavy models.
- **Mac path**: prefer MLX, ONNX, or CPU-friendly runtimes where available.
- **CUDA path**: isolate heavier Qwen3, Chatterbox, and similar backends from the default install.
- **Testing**: conformance and fake-adapter tests must run without downloading large models.

## Governance Principles

- Upstream-first: do not fork model code unless needed for a stable adapter.
- Transparent manifests: every model entry should show license, source, install method, runtime requirements, and caveats.
- Reproducible claims: benchmark claims require raw JSON output and hardware metadata.
- Local-first privacy: user text, generated audio, cloned voice samples, and consent records stay local by default.
- Consent-aware cloning: cloned voices require explicit local provenance metadata.
- Complement existing TTS servers by making tests, manifests, benchmarks, and routing policy reusable.

## Risks

| Risk | Response |
|---|---|
| Existing projects already provide TTS servers | Lead with manifest, benchmark, conformance, registry, and adapter value. |
| Registry maintenance becomes stale | Keep schema small, generate artifacts, and enforce checks in CI. |
| Benchmarks become misleading | Publish raw data with hardware profiles and avoid broad quality claims. |
| Model dependency conflicts | Keep heavyweight adapters optional and isolate them from the default install path. |
| Voice cloning misuse | Require provenance records and expose consent checks before cloning workflows are first-class. |
| Too many models too early | Start with a few backends and make contribution and validation paths excellent. |

## OSS Success Metrics

Early success should not be measured only by stars.

- number of validated model manifests;
- number of backends passing conformance tests;
- number of reproducible benchmark submissions;
- number of external wrappers using the tests or manifest schema;
- time required for a contributor to add a new model adapter;
- issues closed by improving docs, install reliability, and benchmark accuracy;
- real integrations with Open WebUI, Pipecat, LiveKit, or similar voice-agent stacks.
