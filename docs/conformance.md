# Conformance Tests

TimbreGrid conformance checks let any OpenAI-compatible TTS server verify basic `/v1/audio/speech` behavior.

Start a compatible server, then run:

```bash
uv run timbregrid conformance http://localhost:8889/v1 \
  --endpoint audio.speech \
  --model fake:tts \
  --voice alloy \
  --response-format wav \
  --output conformance.json
```

For another server, keep the base URL pointed at that server and set `--model`, `--voice`, and `--response-format` to values it supports.

The command exits with status `0` only when all cases pass. When `--output` is provided, it writes a JSON report with the request payload, status code, content type, content length, elapsed time, and per-case failure message.

The conformance suite is intentionally small and dependency-light so external servers can run it in their own CI before adopting TimbreGrid manifests or benchmark submissions.
