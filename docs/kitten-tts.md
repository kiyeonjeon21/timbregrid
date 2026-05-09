# KittenTTS Adapter

TimbreGrid includes a KittenTTS adapter, but the official KittenTTS wheel is currently distributed from a GitHub release URL. That direct wheel URL is not included in TimbreGrid's published package metadata, so the adapter is installed explicitly from a source checkout.

## Install

```bash
uv sync --all-groups
uv pip install \
  "kittentts @ https://github.com/KittenML/KittenTTS/releases/download/0.8.1/kittentts-0.8.1-py3-none-any.whl" \
  "onnxruntime<1.26"
```

## Smoke Test

```bash
uv run timbregrid models inspect kitten-tts:nano-0.8
uv run timbregrid manifest validate manifests/kitten-tts-nano-0.8.yaml
uv run timbregrid serve --model kitten-tts:nano-0.8 --port 8889
```

Use `response_format="wav"` or `response_format="pcm"` and a KittenTTS voice such as `Jasper`.

## Packaging Note

PyPI and standards-conformant package indexes do not accept published distributions that declare direct URL dependencies. The KittenTTS adapter remains executable when its dependency is installed manually, but `timbregrid[kitten]` is not published as an extra until KittenTTS has an index-hosted install path or TimbreGrid adopts a separate adapter package.
