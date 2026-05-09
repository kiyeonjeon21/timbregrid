# Doctor Reports

`timbregrid doctor` gives a user-facing compatibility diagnosis for an OpenAI-compatible TTS server. It is built on the conformance suite, but its output is easier to read when deciding whether a server is ready for basic `/v1/audio/speech` usage.

Use it against TimbreGrid's reference gateway or another compatible server:

```bash
uvx --from timbregrid==0.1.0a2 timbregrid doctor http://localhost:8889/v1 \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output doctor.json
```

From a TimbreGrid source checkout, use `uv run timbregrid doctor ...`.

The command reports:

- total conformance cases passed and failed;
- basic Open WebUI-style TTS readiness;
- likely Pipecat OpenAI TTS-style readiness;
- the underlying conformance report, including request payloads, status codes, content types, elapsed time, and failures.

Readiness labels are intentionally conservative:

- `ready`: the basic speech request returned audio for the selected model, voice, and response format.
- `likely_ready`: the basic speech request plus common OpenAI TTS fields passed.
- `failed`: at least one required case failed.

`doctor` is not a certification suite for a whole product integration. It checks basic OpenAI-compatible TTS behavior and points to the failed cases when the server does not match the expected shape.

Use `timbregrid conformance` when you need a strict pass/fail suite. Use `timbregrid doctor` when you want a concise report for humans.

For an external-server proof using Speaches, see [`external-server-proof.md`](external-server-proof.md).
