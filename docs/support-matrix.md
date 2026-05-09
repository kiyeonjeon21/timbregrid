# TimbreGrid Model Support Matrix

Generated from `manifests/*.yaml` with `uv run timbregrid registry build`.

| Model | Runtime | Acceleration | Formats | Voices | Multilingual | Long-form | Streaming | Cloning | Commercial use | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `chatterbox:tts` | python / chatterbox-tts | CUDA | wav, pcm | custom | full | limited | no | yes | yes | manifest-only |
| `fake:tts` | python / timbregrid | CPU | mp3, wav, pcm | builtin | limited | limited | no | no | yes | available |
| `kitten-tts:nano-0.8` | python / kittentts | CPU | wav, pcm | builtin | none | limited | no | no | yes | manifest-only |
| `kokoro:82m` | python / kokoro | CPU, CUDA, Metal optional | wav, pcm | builtin | limited | limited | no | no | yes | requires optional dependency: kokoro |
| `qwen3-tts:0.6b-base` | python / qwen-tts | CUDA | wav, pcm | custom | full | limited | yes | yes | yes | manifest-only |
