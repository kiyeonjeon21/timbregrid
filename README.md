# TimbreGrid

> The open compatibility grid for synthetic speech.
> Manifests, benchmarks, conformance tests, routing policy, provenance, and a reference OpenAI-compatible gateway for OSS TTS.

**Status**: spec + static registry + benchmark-aware routing + optional Kokoro adapter MVP implementation
**Research snapshot**: 2026-05-09  
**License (planned)**: MIT for TimbreGrid core; upstream model licenses are preserved per model manifest.

This repository now includes the first spec-first CLI plus a reference OpenAI-compatible TTS gateway backed by a deterministic fake TTS adapter. Kokoro support is available as an optional adapter.

## Current MVP Quickstart

```bash
uv run timbregrid manifest validate manifests/fake-tts.yaml
uv run timbregrid bench fake:tts --suite realtime-agent --output /tmp/timbregrid-bench.json
uv run timbregrid serve --model fake:tts --port 8889
```

In another shell:

```bash
curl http://localhost:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"fake:tts","input":"Hello from TimbreGrid","voice":"alloy","response_format":"wav"}' \
  --output speech.wav
```

The fake adapter generates deterministic local audio bytes without downloading model weights. It is meant for schema, CLI, conformance, benchmark, and SDK compatibility work.

Run the speech conformance suite against the local gateway and write a reusable JSON report:

```bash
uv run timbregrid conformance http://localhost:8889/v1 \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output /tmp/timbregrid-conformance.json
```

Generate the static registry index and support matrix from manifests:

```bash
uv run timbregrid registry build
uv run timbregrid registry build --check
```

- Registry index: [`registry/index.json`](registry/index.json)
- Support matrix: [`docs/support-matrix.md`](docs/support-matrix.md)

Explain benchmark-aware routing for `model="auto"`:

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

Benchmark examples live in [`benchmarks/examples`](benchmarks/examples). If matching benchmark data is missing, `auto` routing falls back to manifest capabilities and availability.

### Docker Quickstart

Run the fake gateway container:

```bash
docker compose up --build
```

In another shell:

```bash
curl http://localhost:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"fake:tts","input":"Hello from Docker","voice":"alloy","response_format":"wav"}' \
  --output docker-speech.wav

uv run timbregrid conformance http://localhost:8889/v1 \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output /tmp/timbregrid-docker-conformance.json
```

The Docker image is intentionally a lightweight `fake:tts` gateway. It does not include Kokoro, `espeak-ng`, or PyTorch-class model dependencies.

### Current MVP Scope

Works today:

- validate TimbreGrid model manifests from YAML;
- generate a static model registry index and support matrix from manifests;
- route `model="auto"` requests by benchmark data, manifest capabilities, response format, availability, and license policy;
- run fake-adapter benchmark suites and write raw JSON output;
- define benchmark prompt suites for realtime-agent, narration, multilingual, cloning, and dialogue;
- include manifest-only registry examples for KittenTTS, Chatterbox, and Qwen3-TTS;
- serve an OpenAI-compatible `POST /v1/audio/speech` endpoint for `fake:tts`;
- run a speech conformance suite with per-case JSON reports against that endpoint;
- verify Python OpenAI SDK compatibility against the local gateway;
- optionally run `kokoro:82m` when `timbregrid[kokoro]` dependencies and `espeak-ng` are installed.

Not included yet:

- KittenTTS, Chatterbox, or Qwen3-TTS inference adapters;
- SQLite metadata storage, hosted registry publishing, or voice provenance storage;
- SSE audio streaming, quality-aware routing, or long-form dialogue routing.

`manifests/kokoro-82m.yaml` is executable only when optional Kokoro dependencies are installed.

### Optional Kokoro Adapter

Install optional Kokoro dependencies:

```bash
uv sync --extra kokoro
```

Kokoro may also require the system `espeak-ng` package. On macOS:

```bash
brew install espeak-ng
```

Then run the first real-model milestone:

```bash
uv run timbregrid models inspect kokoro:82m
uv run timbregrid manifest validate manifests/kokoro-82m.yaml
uv run timbregrid bench kokoro:82m --suite realtime-agent --output /tmp/kokoro.json
uv run timbregrid serve --model kokoro:82m --port 8889
```

Use `response_format="wav"` and a Kokoro voice such as `af_heart` when calling the gateway.

---

## One-Liner

TimbreGrid is an OSS compatibility and evaluation layer for open-source TTS models.

The highest-value OSS artifact is not "another `/v1/audio/speech` server." It is a shared layer that lets model authors, app developers, and self-hosters answer:

- Which TTS model should I use for realtime agents, narration, cloning, edge, or dialogue?
- What does this model support: streaming, cloning, multilingual output, style control, long-form synthesis?
- What hardware, runtime, license, and safety constraints apply?
- Does my server actually behave like the OpenAI speech API?
- Can I route a request to the right local model without hardcoding every backend?

## Name

`TimbreGrid` is meant to describe the infrastructure this project wants to become:

- **Timbre** means the character or color of a voice. That maps to TTS quality, speaker identity, style, and cloning better than generic "audio" or "speech."
- **Grid** means a compatibility matrix across models, runtimes, hardware, voices, licenses, benchmarks, and policies.

Use `TimbreGrid` for the project name and `timbregrid` for the repo, package, Docker image, and CLI. Before publishing packages, verify GitHub, PyPI, npm, Homebrew, Docker Hub/GHCR, domain, and trademark availability.

## Thesis

OSS TTS no longer lacks models. It lacks operational standards.

Current ecosystem signals:

- **Speaches** already positions itself as "Ollama, but for TTS/STT models" and exposes OpenAI-compatible speech endpoints.
- **LocalAI** supports OpenAI-compatible TTS, ElevenLabs-style compatibility, and streaming TTS.
- **Vox / vox-runtime** is already a local runtime for STT/TTS models with pull-on-demand adapters, custom voices, REST/WebSocket/gRPC, and OpenAI-compatible endpoints.
- Many single-model wrappers expose `/v1/audio/speech` for Dia, Orpheus, VibeVoice, Chatterbox, and other models.
- Model releases now move quickly across Kokoro, Qwen3-TTS, Chatterbox, KittenTTS, MOSS, SoulX, VibeVoice, and related families.

That means TimbreGrid should not compete on the shallow claim of API compatibility alone. Its OSS value is stronger if it becomes the **compatibility, benchmark, registry, and governance layer** that other TTS runtimes can also benefit from.

## North Star Vision

The challenging version of this project is not a better local server. It is the missing public infrastructure for synthetic speech.

In the mature version:

- every serious OSS TTS release ships a machine-readable TimbreGrid manifest;
- every local TTS server can run the same OpenAI speech conformance suite;
- every benchmark claim includes raw latency, memory, quality-proxy, hardware, quantization, and runtime metadata;
- every cloned or imported voice has a local provenance record with consent, allowed use, source hashes, and optional watermark evidence;
- every voice-agent stack can choose a TTS backend by policy instead of by hardcoded model name;
- every developer can answer "what should I run on this machine for this voice job?" with measured data.

The long-term bet:

> Synthetic speech needs the equivalent of package metadata, CI compatibility tests, and supply-chain policy. TimbreGrid can become that layer for open TTS.

This makes the project more ambitious than a runtime:

- **Model registry** becomes a public compatibility graph.
- **Benchmark harness** becomes a reproducibility standard.
- **Voice provenance** becomes a local trust layer for cloning.
- **Routing** becomes policy-driven speech infrastructure.
- **Reference gateway** becomes just one implementation of the spec.

## OSS Value

TimbreGrid should create value even for people who never use the gateway.

| OSS artifact | Who benefits | Why it matters |
|---|---|---|
| Model manifest schema | model authors, server authors, app developers | standardizes license, runtime, capabilities, caveats, voices, and hardware requirements |
| Benchmark harness | developers, maintainers, researchers | makes latency, real-time factor, memory, failures, and quality proxies reproducible |
| OpenAI speech conformance tests | Speaches-style servers, wrappers, apps | checks whether `/v1/audio/speech` behavior matches SDK expectations |
| Adapter SDK | contributors, model authors | lowers the work needed to add a new backend without rewriting the gateway |
| Routing policy engine | voice-agent developers | chooses models by purpose, hardware, license policy, and benchmark data |
| Voice provenance library | teams using cloning | tracks source, consent, license, references, and watermark hooks locally |

The project should be useful as:

1. a **spec** for describing TTS model capabilities;
2. a **test suite** for OpenAI-compatible TTS servers;
3. a **benchmark CLI** for local TTS models;
4. a **reference runtime** for serving and routing models;
5. a **governed local voice library** for self-hosted voice agents.

## Target Users

- TTS model authors who want a standard way to publish runtime requirements and capabilities.
- Voice-agent developers who need to choose between fast, expressive, cloning, edge, and long-form TTS models.
- Self-hosters who want local speech generation without losing track of license and hardware constraints.
- Maintainers of OpenAI-compatible TTS servers who want a reusable conformance suite.
- Teams experimenting with voice cloning who need local provenance and consent records from the start.

## Non-Goals

TimbreGrid should stay focused early.

- Not a general LLM gateway. Use LiteLLM, LocalAI, Ollama, vLLM, or llama.cpp for that.
- Not an STT platform in the MVP. Speaches and LocalAI already cover broader STT/TTS surfaces.
- Not a claim to be the first OpenAI-compatible TTS server.
- Not a hosted cloud service first.
- Not a public voice marketplace with unclear consent or licensing.
- Not a benchmark leaderboard without reproducible raw data.

## Ecosystem Position

TimbreGrid should complement existing OSS projects instead of pretending they do not exist.

| Project type | Examples | What they do well | TimbreGrid gap to fill |
|---|---|---|---|
| Speech server | Speaches | OpenAI-compatible STT/TTS server, self-hosted speech API | reusable manifests, richer TTS benchmarking, policy routing, voice provenance |
| Speech runtime | Vox / vox-runtime | local STT/TTS runtime, pull-on-demand adapters, custom voices, multiple transports | independent conformance suite, benchmark standard, voice provenance policy, registry metadata usable outside one runtime |
| All-in-one local AI | LocalAI | broad OpenAI-compatible local AI server, many backends | TTS-specific conformance, model comparison, governed voice records |
| Provider gateway | LiteLLM | routing and spend controls across cloud/provider APIs | local OSS TTS inference, model manifests, voice governance |
| Single-model wrapper | Dia, Orpheus, VibeVoice, Chatterbox wrappers | fast path to run one model | shared adapter contract, tests, benchmarks, routing across families |
| Model repo | Kokoro, Qwen3-TTS, KittenTTS, MOSS, SoulX | model weights and demos | install/runtime metadata, capability flags, benchmark profiles |

The defensible claim:

> TimbreGrid is the open compatibility and evaluation layer for OSS TTS, with a reference OpenAI-compatible runtime.

## Model Landscape

Different TTS model families optimize for different jobs. TimbreGrid should encode those differences in manifests and benchmark data instead of hardcoding marketing claims.

| Model family | Current signal | Likely lane |
|---|---|---|
| Kokoro-82M | 82M open-weight TTS, Apache 2.0, lightweight and fast | default realtime / CPU-friendly baseline |
| Qwen3-TTS | Apache 2.0 technical report; streaming, multilingual, 3-second voice cloning, 97ms first-packet target in paper | low-latency multilingual and cloning |
| Chatterbox | MIT, easy `pip install`, expressive speech, built-in neural watermarking | expressive speech and cloning |
| KittenTTS | 15M nano model, 25 MB int8 variant | edge, mobile, cheap CPU |
| MOSS-TTS / MOSS-TTSD | Apache 2.0 family; long-form dialogue, 1-5 speakers, up to 60-minute context, SGLang acceleration | long-form podcast / dialogue |
| SoulX-Podcast | Apache 2.0; multi-turn, multi-speaker podcast synthesis with Chinese dialect cloning | podcast and dialect-specialized expansion |
| VibeVoice | MIT repo, long-form and realtime models; TTS code availability has changed due to responsible-use concerns | watchlist until registry can validate availability and risk |

## Core Deliverables

### 1. Model Manifest

A model manifest should be the foundation of the project. It is useful even without the gateway.

```yaml
schema_version: 0.1
id: kokoro:82m
name: Kokoro 82M
upstream:
  homepage: https://huggingface.co/hexgrad/Kokoro-82M
  license: apache-2.0
  weights: open-weight
runtime:
  kind: python
  package: kokoro
  acceleration:
    cpu: true
    cuda: true
    metal: optional
capabilities:
  streaming: false
  voice_cloning: false
  multilingual: limited
  long_form: limited
  style_control: speed
  formats: [wav, pcm]
audio:
  sample_rate_hz: 24000
  formats: [wav, pcm]
voices:
  builtin: true
  custom: false
policy:
  commercial_use: true
  requires_voice_consent: false
notes:
  - "Good baseline for low-latency local TTS."
```

Manifest goals:

- make model support reviewable through pull requests;
- make licenses and caveats explicit;
- make routing possible without backend-specific code;
- make benchmarks comparable by model version and hardware profile.

### 2. Benchmark Harness

The benchmark CLI should be a first-class OSS artifact.

```bash
timbregrid bench kokoro:82m \
  --suite realtime-agent \
  --hardware auto \
  --format json \
  --output benches/kokoro-82m.m2-pro.json
```

Minimum metrics:

- time to first audio;
- total generation time;
- real-time factor;
- memory peak;
- output duration;
- sample rate and format;
- streaming support and chunk cadence where applicable;
- failure rate across a prompt suite.

Benchmark principles:

- publish raw JSON, not only summary tables;
- include hardware, OS, driver, model version, quantization, and runtime version;
- avoid "SOTA" claims unless backed by reproducible evals;
- support local-only benchmarking without sending text or audio to a cloud service.

### 3. OpenAI Speech Conformance

TimbreGrid should provide tests that any OpenAI-compatible TTS server can run.

```bash
timbregrid conformance http://localhost:8889/v1 \
  --endpoint audio.speech \
  --sdk python
```

Initial coverage:

- accepts required fields: `model`, `input`, `voice`;
- handles `response_format`;
- handles `speed` range validation;
- handles `stream_format` capability flags;
- returns audio bytes with correct content type;
- returns OpenAI-shaped errors where practical;
- works with the official OpenAI SDK using `base_url`.

This creates OSS value beyond TimbreGrid's own runtime.

### 4. Adapter SDK

Every backend should implement a small common contract.

```python
class TTSAdapter:
    id: str

    def load(self) -> None: ...

    def synthesize(self, request: SpeechRequest) -> SpeechResult: ...

    def stream(self, request: SpeechRequest) -> AudioStream: ...

    def voices(self) -> list[VoiceInfo]: ...

    def capabilities(self) -> Capabilities: ...
```

Adapter goals:

- model wrappers stay small;
- dependency conflicts can be isolated;
- capability flags are explicit;
- conformance and benchmark tools can test every backend consistently.

### 5. Reference Gateway

The gateway is still useful, but it should be framed as the reference implementation of the spec.

It should implement OpenAI's `POST /v1/audio/speech` shape first:

- required: `model`, `input`, `voice`;
- useful parity fields: `response_format`, `speed`, `stream_format`, `instructions`;
- response: audio bytes by default, SSE when `stream_format="sse"` is requested and the backend supports it.

TimbreGrid-specific routing should live behind OpenAI SDK escape hatches such as `extra_body`.

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8889/v1", api_key="local")

audio = client.audio.speech.create(
    model="auto",
    voice="af_heart",
    input="Hello from a local open-source TTS runtime.",
    response_format="wav",
    extra_body={
        "purpose": "realtime",
        "target_latency_ms": 350,
        "license_policy": "commercial_ok",
        "hardware_profile": "generic-ci",
    },
)

with open("reply.wav", "wb") as f:
    f.write(audio.read())
```

Proposed routing extensions:

| Field | Purpose |
|---|---|
| `purpose` | `realtime`, `narration`, `cloning`, `dialogue`, `edge`, `multilingual` |
| `target_latency_ms` | routing hint for first audio latency |
| `license_policy` | `any`, `commercial_ok`, `permissive_only`, `research_only` |
| `hardware_profile` | optional profile selector for matching benchmark artifacts |
| `voice_ref` | path, URL, or managed voice ID for models that support cloning |
| `consent_id` | local consent/provenance record for cloned voices |
| `seed` | reproducibility where backend supports it |
| `script_format` | `plain`, `ssml-lite`, `dialogue` for long-form models |

### 6. Voice Provenance

Voice cloning makes OSS TTS more useful, but also more fragile. TimbreGrid should treat provenance as a core local data model, not a later enterprise feature.

Voice records should include:

- `voice_id`;
- display name and tags;
- source type: built-in, imported, cloned, generated;
- source URL or local path;
- license;
- consent/provenance record;
- allowed use: personal, commercial, research, internal;
- reference sample hashes;
- watermark detector results where supported.

Default stance:

- no bundled public voice library unless license and provenance are explicit;
- cloned voices stay local by default;
- cloning requests can require `consent_id`;
- unsafe or unclear models can remain outside the default registry.

## Architecture

```
┌──────────────────────────────┐
│ TimbreGrid OSS core          │
│                              │
│ ┌ manifest schema            │
│ ├ conformance tests          │
│ ├ benchmark harness          │
│ ├ adapter SDK                │
│ ├ registry index             │
│ └ voice provenance store     │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Reference gateway            │
│ FastAPI + ASGI streaming     │
│ OpenAI /v1/audio/speech      │
└───────┬──────────────┬───────┘
        │              │
        ▼              ▼
┌──────────────┐  ┌──────────────┐
│ lightweight  │  │ isolated      │
│ adapters     │  │ workers       │
│ ONNX / MLX   │  │ Docker / uv   │
└──────┬───────┘  └──────┬───────┘
       ▼                 ▼
 Kokoro / Kitten    Qwen3 / Chatterbox / MOSS
```

Initial implementation should prefer **FastAPI** because the model wrappers and audio tooling are Python-heavy. Go can be revisited after the gateway contract stabilizes.

## Codex Project Workflow

This repo includes project-scoped Codex setup so future implementation sessions can continue from the README roadmap without rebuilding the working rules from scratch.

- `AGENTS.md` defines durable repo instructions for roadmap use, generated files, and validation.
- `.agents/skills/timbregrid-roadmap` guides "what remains / next milestone / continue from README" work.
- `.agents/skills/timbregrid-validation` maps changed areas to the smallest relevant validation commands.
- `.codex/agents` defines read-only custom agents for explicit subagent workflows.
- `.codex/hooks` provides advisory reminders for roadmap hygiene.

See [`docs/codex-workflow.md`](docs/codex-workflow.md) for the management model.

## Development Roadmap

### Phase 0: Spec-First Planning

- [x] define `timbregrid.model.yaml` manifest schema;
- [x] define `SpeechRequest`, `SpeechResult`, `Capabilities`, and `VoiceInfo`;
- [x] define benchmark prompt suites: realtime-agent, narration, multilingual, cloning, dialogue;
- [x] define OpenAI speech conformance cases;
- [x] create example manifests for Kokoro, KittenTTS, Chatterbox, Qwen3-TTS.

### Phase 1: Useful OSS Before Runtime

- [x] `timbregrid manifest validate`;
- [x] `timbregrid bench` against a local adapter;
- [x] `timbregrid conformance` against an existing OpenAI-compatible TTS server;
- [ ] publish raw benchmark JSON examples for Apple Silicon, CPU, and CUDA where available (partial: deterministic fake benchmark example exists);
- [ ] document how other servers can use the tests (partial: JSON conformance reports are implemented).

### Phase 2: Reference Gateway MVP

- [x] `POST /v1/audio/speech` compatible endpoint;
- [x] Kokoro adapter as the first fast baseline (optional `timbregrid[kokoro]`);
- [ ] KittenTTS adapter for edge/CPU lane;
- [ ] one expressive or cloning backend: Chatterbox or Qwen3-TTS;
- [ ] `model="auto"` routing by purpose, hardware, license policy, and benchmark data (partial: benchmark-aware routing uses raw benchmark JSON when available, then falls back to manifest-first routing);
- [x] Docker image with one-command local serving for the fake gateway.

### Phase 3: Community Registry

- [ ] hosted static registry index (partial: local `registry/index.json` is generated from manifests);
- [ ] manifest PR template;
- [ ] CI validation for manifest schema, links, checksums, licenses, and install smoke tests (partial: tests, manifest validation, registry drift check, and fake benchmark smoke run in CI);
- [x] model support matrix generated from manifests;
- [ ] benchmark result submission format.

### Phase 4: Voice Governance And Integrations

- [ ] local voice records and `/v1/audio/voices`;
- [ ] consent/provenance enforcement hooks;
- [ ] Open WebUI, Pipecat, LiveKit, and direct OpenAI SDK examples;
- [ ] WebUI for A/B tests, latency view, and voice preview.

## First Milestone

The first public milestone should be small, testable, and useful outside this repo:

```bash
uv sync --extra kokoro
uv run timbregrid models inspect kokoro:82m
uv run timbregrid manifest validate manifests/kokoro-82m.yaml
uv run timbregrid bench kokoro:82m --suite realtime-agent --output kokoro.json
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
- the benchmark output is reproducible;
- another TTS server could run the same conformance tests;
- the project has value before adding five more models.

## Next Milestones

1. **Voice provenance**: add local voice records, consent metadata, and `/v1/audio/voices`.
2. **Manifest contribution path**: add a PR template and broader manifest validation for external model submissions.
3. **Benchmark submissions**: define contribution format and CI checks for broader hardware benchmark data.

## Technical Choices

- **Core language**: Python first, because model wrappers and audio tooling are Python-heavy.
- **Gateway**: FastAPI + ASGI streaming.
- **Manifest format**: YAML for authoring, JSON schema for validation.
- **Storage**: SQLite for model, voice, and benchmark metadata; filesystem for model cache and audio artifacts.
- **Runtime isolation**: in-process for small ONNX/MLX models; sidecar workers or containers for PyTorch-heavy models.
- **Mac path**: MLX/ONNX where available.
- **CUDA path**: containerized workers for Qwen3, Chatterbox, and MOSS-class models.
- **Testing**: conformance tests should run without downloading large models.

## Governance Principles

- Upstream-first: do not fork model code unless needed for a stable adapter.
- Transparent manifests: every model entry must show license, source, install method, and known caveats.
- Reproducible claims: benchmark claims require raw output and hardware metadata.
- Local-first privacy: user text, generated audio, and cloned voice samples stay local by default.
- Consent-aware cloning: cloned voices require explicit local provenance metadata.
- Complement, do not erase: make tools that Speaches, Vox, LocalAI, and single-model wrappers can reuse.

## Risks

| Risk | Response |
|---|---|
| Existing projects already provide TTS servers | lead with manifest, benchmark, conformance, and adapter value |
| Registry maintenance becomes stale | keep schema small, use CI validation, require upstream version metadata |
| Benchmarks become misleading | publish raw data and hardware profiles; avoid broad quality claims |
| Model dependency conflicts | isolate heavyweight adapters; prefer ONNX/MLX for small local models |
| Voice cloning misuse | require provenance records and expose watermark checks where supported |
| Too many models too early | start with 2-3 backends and make the contribution path excellent |
| Cloud monetization distracts from OSS | postpone cloud until the OSS spec and tooling are adopted |

## OSS Success Metrics

Early success should not be measured only by stars.

- number of validated model manifests;
- number of backends passing conformance tests;
- number of reproducible benchmark submissions;
- number of external wrappers using the tests or manifest schema;
- time required for a contributor to add a new model adapter;
- issues closed by improving docs, install reliability, and benchmark accuracy;
- real integrations with Open WebUI, Pipecat, LiveKit, or similar voice-agent stacks.

## Sustainability

The OSS core should remain useful without a paid service.

Potential later sustainability paths:

1. hosted signed registry and compatibility CI;
2. managed benchmark runners across common hardware profiles;
3. private registry and policy packs for teams;
4. managed inference only after the local OSS workflow is credible.

## Open Questions

- Should the project be TTS-only for the first 3 months? Recommendation: yes.
- Should the first public artifact be the gateway or the benchmark/conformance kit? Recommendation: benchmark/conformance first, with the gateway as a reference implementation.
- Which second backend after Kokoro? Recommendation: KittenTTS for edge plus Chatterbox or Qwen3-TTS for expressive/cloning.
- Should public voices ship by default? Recommendation: no, only explicit-license examples and local user imports.
- Should the project compare against Speaches and Vox? Recommendation: yes, but with measured scope and reusable tests instead of broad positioning claims.

## References

- OpenAI speech API reference: https://platform.openai.com/docs/api-reference/audio/createSpeech
- OpenAI text-to-speech guide: https://platform.openai.com/docs/guides/text-to-speech
- Speaches: https://github.com/speaches-ai/speaches
- Vox runtime: https://pypi.org/project/vox-runtime/
- LocalAI TTS: https://localai.io/features/text-to-audio/
- LiteLLM docs: https://docs.litellm.ai/
- Kokoro-82M: https://huggingface.co/hexgrad/Kokoro-82M
- Qwen3-TTS technical report: https://arxiv.org/abs/2601.15621
- Chatterbox: https://github.com/resemble-ai/chatterbox
- KittenTTS: https://github.com/KittenML/KittenTTS
- MOSS-TTSD: https://github.com/OpenMOSS/MOSS-TTSD
- SoulX-Podcast: https://huggingface.co/Soul-AILab/SoulX-Podcast-1.7B
- VibeVoice: https://github.com/microsoft/VibeVoice

## Original Notes

- 원본 ideation: [`~/dev/personal/notes/ideas/docs/spokesync.md`](../../notes/ideas/docs/spokesync.md)
- 부모 번들: [`~/dev/personal/notes/ideas/docs/stt-tts-oss-2026-05.md`](../../notes/ideas/docs/stt-tts-oss-2026-05.md)
