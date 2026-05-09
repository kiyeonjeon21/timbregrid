# External Server Proof

TimbreGrid is useful even when you do not use its reference gateway. The point of `timbregrid doctor` is to diagnose an existing OpenAI-compatible TTS server and produce a report you can inspect before wiring that server into Open WebUI, Pipecat, or another voice stack.

This guide uses Speaches as the first external proof target because Speaches is an OpenAI API-compatible speech server with Kokoro and Piper TTS support.

Generated reports should go under `demo-assets/`, which is ignored by git.

## Start Speaches

Follow the Speaches installation guide for the target machine. A CPU Docker run from the official docs looks like:

```bash
docker run \
  --rm \
  --detach \
  --publish 8000:8000 \
  --name speaches \
  --volume hf-hub-cache:/home/ubuntu/.cache/huggingface/hub \
  ghcr.io/speaches-ai/speaches:latest-cpu
```

Download a TTS model through Speaches:

```bash
export SPEACHES_BASE_URL="http://localhost:8000"
uvx speaches-cli registry ls --task text-to-speech
uvx speaches-cli model download speaches-ai/Kokoro-82M-v1.0-ONNX
uvx speaches-cli model ls --task text-to-speech
```

## Confirm The Server Directly

```bash
mkdir -p demo-assets

curl "$SPEACHES_BASE_URL/v1/audio/speech" \
  -H "Content-Type: application/json" \
  --output demo-assets/speaches-direct.wav \
  --data '{
    "model": "speaches-ai/Kokoro-82M-v1.0-ONNX",
    "voice": "af_heart",
    "input": "Hello from Speaches through an OpenAI compatible speech endpoint.",
    "response_format": "wav"
  }'
```

## Run TimbreGrid Doctor

```bash
uvx --from timbregrid==0.1.0a2 timbregrid doctor "$SPEACHES_BASE_URL/v1" \
  --model speaches-ai/Kokoro-82M-v1.0-ONNX \
  --voice af_heart \
  --response-format wav \
  --output demo-assets/speaches-doctor.json
```

From a TimbreGrid source checkout, `uv run timbregrid doctor ...` is equivalent.

Expected shape:

```text
OK doctor: 11/11 conformance cases passed
open_webui_tts: ready - basic OpenAI-compatible /v1/audio/speech request returned audio
pipecat_openai_tts: likely_ready - OpenAI-style speech request, speed, and instructions fields passed basic checks
```

If the result fails, inspect the underlying cases:

```bash
jq '.summary, .integration_readiness, .conformance.cases[] | {name, passed, status_code, content_type, failure}' \
  demo-assets/speaches-doctor.json
```

You can also open [`../examples/doctor-report-viewer.html`](../examples/doctor-report-viewer.html) in a browser and drop `demo-assets/speaches-doctor.json` into it.

## Use The Report

- `open_webui_tts: ready` means the selected Speaches model, voice, and response format passed TimbreGrid's basic OpenAI-compatible TTS checks.
- `pipecat_openai_tts: likely_ready` means the basic request plus common OpenAI TTS fields passed; it is still not a full Pipecat integration certification.
- Any `failed` status should be fixed at the server/configuration level before changing Open WebUI or voice-agent settings.

Do not commit `demo-assets/speaches-doctor.json` unless the project later creates a dedicated, reviewed external-server report directory. Local reports depend on host hardware, server version, model cache state, and selected voice.

## References

- Speaches introduction: <https://speaches.ai/>
- Speaches installation: <https://speaches.ai/installation/>
- Speaches text-to-speech usage: <https://speaches.ai/usage/text-to-speech/>
- Speaches model discovery: <https://speaches.ai/usage/model-discovery/>
