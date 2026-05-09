---
name: timbregrid-validation
description: Use before finalizing TimbreGrid changes to choose and run the smallest relevant validation set for code, manifests, registry, gateway, routing, Docker, or docs changes.
---

# TimbreGrid Validation Workflow

Use this skill after implementation and before finalizing a response.

## Baseline

1. Inspect changed files with `git status --short`.
2. Pick validations by touched area.
3. Run the smallest set that covers the behavioral risk.
4. Report exact commands and whether each passed, failed, or was skipped.

## Validation Matrix

- Any Python behavior in `src/` or `tests/`:
  - `uv run pytest`
- Manifest or schema changes in `manifests/` or `schemas/`:
  - `uv run timbregrid manifest validate <changed-manifest>`
  - `uv run timbregrid registry build --check`
  - `uv run pytest tests/test_manifest.py tests/test_registry_index.py`
- Registry or support matrix changes:
  - `uv run timbregrid registry build --check`
  - `uv run pytest tests/test_registry_index.py`
- Routing or benchmark changes:
  - `uv run pytest tests/test_routing.py tests/test_benchmark_store.py tests/test_cli.py`
  - run a representative `uv run timbregrid route explain ...` command when CLI behavior changes
- Gateway, conformance, or OpenAI SDK compatibility changes:
  - `uv run pytest tests/test_gateway.py tests/test_conformance.py tests/test_openai_sdk.py`
- Adapter changes:
  - fake adapter: `uv run pytest tests/test_fake_adapter.py`
  - Kokoro adapter: `uv run pytest tests/test_kokoro_adapter.py`; only run real optional dependency smoke checks when the optional environment is installed
- Docker changes:
  - `docker compose build`
  - run a gateway smoke request when feasible
- Docs-only changes:
  - no runtime tests required unless docs include changed commands; verify commands against existing CLI names when practical

## Reporting

- Do not say validation passed unless the command actually ran and passed.
- If a command is skipped because dependencies, Docker, or optional model packages are unavailable, say that directly.
- If only a subset ran, name the residual risk.
