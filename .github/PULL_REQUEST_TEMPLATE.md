# Summary

- 

# Change Type

- [ ] Manifest or registry
- [ ] Benchmark or conformance
- [ ] Gateway or routing
- [ ] Adapter
- [ ] Documentation

# Validation

- [ ] `uv run pytest`
- [ ] `uv run timbregrid registry build --check`
- [ ] `uv run timbregrid manifest validate manifests/<model>.yaml`
- [ ] `uv run timbregrid bench validate <file>.json`
- [ ] Optional adapter smoke test, if applicable

# Manifest Checklist

- [ ] Upstream homepage and license are included.
- [ ] Runtime package and acceleration requirements are accurate.
- [ ] Audio formats and sample rate are listed.
- [ ] Voice, cloning, multilingual, long-form, streaming, and style-control flags are explicit.
- [ ] Commercial-use and consent requirements are explicit.

# Benchmark Checklist

- [ ] Benchmark JSON was produced by `uv run timbregrid bench`.
- [ ] Hardware metadata is present.
- [ ] Metrics are not hand-edited.
- [ ] Fake or synthetic examples are clearly labeled.

# Safety

- [ ] No private voice samples, consent records, API keys, tokens, or private datasets are included.
