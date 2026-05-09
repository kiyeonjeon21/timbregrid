# Open WebUI Integration

TimbreGrid can act as a local OpenAI-compatible text-to-speech backend for Open WebUI's audio settings.

This guide covers TTS only. TimbreGrid currently provides `/v1/audio/speech`; it does not provide chat completions, speech-to-text, or streaming audio endpoints.

## Start TimbreGrid

For a dependency-light smoke test:

```bash
uv sync --all-groups
uv run timbregrid serve --model fake:tts --port 8889
```

For KittenTTS:

```bash
uv sync --all-groups --extra kitten
uv run timbregrid serve --model kitten-tts:nano-0.8 --port 8889
```

For Kokoro:

```bash
uv sync --all-groups --extra kokoro
uv run timbregrid serve --model kokoro:82m --port 8889
```

Kokoro may also require `espeak-ng` on the host.

## Verify The TTS Endpoint

```bash
curl http://127.0.0.1:8889/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"kitten-tts:nano-0.8","input":"Hello from Open WebUI through TimbreGrid.","voice":"Jasper","response_format":"wav"}' \
  --output open-webui-tts.wav
```

For the fake adapter, use `model="fake:tts"` and `voice="alloy"`. For Kokoro, use `model="kokoro:82m"` and a Kokoro voice such as `af_heart`.

## Preflight: Verify Compatibility With `timbregrid doctor`

Before configuring Open WebUI, confirm TimbreGrid answers `/v1/audio/speech` the way Open WebUI expects:

```bash
uv run timbregrid doctor http://127.0.0.1:8889/v1 \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output doctor.json
```

Use `--model kitten-tts:nano-0.8 --voice Jasper` for KittenTTS or `--model kokoro:82m --voice af_heart` for Kokoro.

The command prints a per-integration readiness line. Look for `open_webui_tts`:

```text
OK doctor: 9/9 conformance cases passed
open_webui_tts: ready - basic OpenAI-compatible /v1/audio/speech request returned audio
pipecat_openai_tts: likely_ready - OpenAI-style speech request, speed, and instructions fields passed basic checks
```

`ready` means it is safe to proceed to the Admin Panel steps below. `failed` means Open WebUI will not work with this configuration; open `doctor.json` and inspect `conformance.cases[].failure_reason` for the underlying cause before changing anything in Open WebUI.

See [`docs/doctor.md`](../doctor.md) for the full readiness label semantics.

## Configure Open WebUI

In Open WebUI, open `Admin Panel` -> `Settings` -> `Audio` and set:

| Setting | Value |
|---|---|
| Text-to-Speech Engine | `OpenAI` |
| API Base URL | `http://127.0.0.1:8889/v1` |
| API Key | `local` |
| TTS Model | `kitten-tts:nano-0.8` |
| TTS Voice | `Jasper` |
| OpenAI TTS Params | `{"response_format":"wav"}` |

If Open WebUI runs in Docker Desktop and TimbreGrid runs on the host, use:

```text
http://host.docker.internal:8889/v1
```

With environment variables:

```yaml
environment:
  - AUDIO_TTS_ENGINE=openai
  - AUDIO_TTS_OPENAI_API_BASE_URL=http://host.docker.internal:8889/v1
  - AUDIO_TTS_OPENAI_API_KEY=local
  - AUDIO_TTS_MODEL=kitten-tts:nano-0.8
  - AUDIO_TTS_VOICE=Jasper
  - AUDIO_TTS_OPENAI_PARAMS={"response_format":"wav"}
```

Use `http://127.0.0.1:8889/v1` instead when Open WebUI is not running inside Docker.

## Notes

- For a one-command both-stack run, see [`examples/open-webui-compose.yml`](../../examples/open-webui-compose.yml). It boots TimbreGrid (with `fake:tts`) and Open WebUI together with the right `AUDIO_TTS_*` env vars already wired up.
- Open WebUI must be able to reach the TimbreGrid process from its own network namespace.
- Set `response_format` to `wav` for Kokoro and KittenTTS. The OpenAI TTS default is often `mp3`, which those adapters do not currently emit.
- TimbreGrid validates known voices for the selected model. Use `/v1/audio/voices?model=<model-id>` to list available voices.
- The fake adapter is for compatibility checks and generates deterministic test audio, not natural speech.
- Real model performance depends on the host machine and optional dependencies. Treat benchmark submissions as raw evidence, not guarantees.

References:

- Open WebUI OpenAI-compatible provider docs: https://docs.openwebui.com/getting-started/quick-start/connect-a-provider/starting-with-openai-compatible/
- Open WebUI audio troubleshooting docs: https://docs.openwebui.com/troubleshooting/audio
