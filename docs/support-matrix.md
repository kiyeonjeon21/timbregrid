# TimbreGrid Model Support Matrix

Generated from `manifests/*.yaml` with `uv run timbregrid registry build`.

| Model | Runtime | Acceleration | Formats | Voices | Multilingual | Long-form | Streaming | Cloning | Commercial use | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `fake:tts` | python / timbregrid | CPU | mp3, wav, pcm | builtin | limited | limited | no | no | yes | available |
| `kokoro:82m` | python / kokoro | CPU, CUDA, Metal optional | wav, pcm | builtin | limited | limited | no | no | yes | requires optional dependency: kokoro |
