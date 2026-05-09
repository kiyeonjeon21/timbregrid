# TimbreGrid Agent Instructions

## Project Source Of Truth

- Treat `README.md` as the source of truth for product scope, status, and roadmap state.
- Before planning or implementing roadmap work, read `README.md` sections `Current MVP Scope`, `Development Roadmap`, `First Milestone`, and `Next Milestones`.
- When a roadmap checkbox or partial milestone becomes true, update `README.md` in the same change.
- Keep README status conservative: mark an item complete only after the implementation and relevant validation have both landed.

## Implementation Workflow

- Start with `git status --short` and preserve unrelated user changes.
- Prefer the first relevant unfinished roadmap item unless the user names a different scope.
- Keep changes small and aligned with existing `src/timbregrid` patterns.
- Do not manually edit generated registry artifacts. Regenerate them with `uv run timbregrid registry build` and verify with `uv run timbregrid registry build --check`.
- Do not add heavyweight model dependencies to the default install path. Keep real model adapters optional.

## Validation

- Python behavior changes: run `uv run pytest`.
- Manifest, schema, registry, or support-matrix changes: run manifest validation for changed manifests and `uv run timbregrid registry build --check`.
- Routing or benchmark changes: include routing and benchmark tests, or run the full test suite if the impact is shared.
- Gateway, conformance, or SDK compatibility changes: run the relevant gateway/conformance/OpenAI SDK tests.
- Docker changes: run a Docker build or compose smoke test when feasible.
- If validation cannot be run, state the exact reason and the residual risk.

## Codex Project Setup

- Use `.agents/skills/timbregrid-roadmap` when the user asks what remains, what to do next, or to continue from README/ROADMAP phases.
- Use `.agents/skills/timbregrid-validation` before finalizing implementation work.
- Use project custom agents in `.codex/agents` only when the user explicitly asks for subagents or parallel agent work.
- Hooks under `.codex/hooks` are advisory guardrails; deterministic enforcement should still live in tests, CI, and project commands.
