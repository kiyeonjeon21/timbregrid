# Real Audio Demo

The Docker quickstart uses `fake:tts` so compatibility checks work without model downloads. Use this guide when you want a real local voice demo with Kokoro.

Generated audio should go under `demo-assets/`, which is ignored by git.

## Setup

Install TimbreGrid with the Kokoro optional extra:

```bash
uv sync --all-groups --extra kokoro
mkdir -p demo-assets
```

Kokoro also needs `espeak-ng` on many systems. On macOS:

```bash
brew install espeak-ng
```

Confirm the adapter is visible:

```bash
uv run timbregrid models inspect kokoro:82m
uv run timbregrid manifest validate manifests/kokoro-82m.yaml
```

## Start The Gateway

In one terminal:

```bash
uv run timbregrid serve --model kokoro:82m --port 8889
```

In another terminal:

```bash
curl -fsS http://localhost:8889/health
curl -fsS "http://localhost:8889/v1/audio/voices?model=kokoro:82m"
```

## Generate Speech

```bash
curl http://localhost:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"kokoro:82m","input":"Hello from TimbreGrid using Kokoro","voice":"af_heart","response_format":"wav"}' \
  --output demo-assets/kokoro-demo.wav
```

Check the result:

```bash
ls -lh demo-assets/kokoro-demo.wav
```

You can also use the OpenAI Python SDK example against the running gateway:

```bash
TIMBREGRID_MODEL=kokoro:82m \
TIMBREGRID_VOICE=af_heart \
TIMBREGRID_OUTPUT=demo-assets/openai-sdk-kokoro.wav \
uv run python examples/openai_sdk_speech.py
```

## Optional Benchmark

Run this only when you want a local benchmark artifact from the current machine:

```bash
uv run timbregrid bench kokoro:82m \
  --suite realtime-agent \
  --hardware-profile cpu \
  --output demo-assets/kokoro-realtime-agent.json

uv run timbregrid bench validate demo-assets/kokoro-realtime-agent.json
```

Do not commit generated audio or local benchmark files unless a benchmark submission is intentionally prepared as raw JSON under `benchmarks/submissions`.

## Troubleshooting

If `kokoro` imports but synthesis fails, confirm `espeak-ng` is installed and available on `PATH`.

If port `8889` is already in use, start the gateway with another port and update the URLs:

```bash
uv run timbregrid serve --model kokoro:82m --port 8890
```

If you later install another optional extra, include every optional adapter you want to keep in the same sync command:

```bash
uv sync --all-groups --extra kokoro --extra kitten
```
