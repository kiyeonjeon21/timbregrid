---
name: timbregrid-roadmap
description: Use when working from TimbreGrid README roadmap phases, deciding what remains, planning the next milestone, or continuing implementation from the README.
---

# TimbreGrid Roadmap Workflow

Use this skill when the task mentions roadmap, phase, milestone, README, remaining work, next work, or continuing implementation.

## Inputs

- `README.md`
- Current git status
- Relevant source, tests, manifests, schemas, benchmark examples, registry files, and docs

## Steps

1. Read `README.md` sections `Current MVP Scope`, `Development Roadmap`, `First Milestone`, and `Next Milestones`.
2. Identify the first unfinished roadmap item that matches the user's request. Prefer high-value project infrastructure over adding many model adapters early.
3. Classify the item as one of:
   - `complete`: implementation and validation are present;
   - `partial`: some implementation exists but README still names missing scope;
   - `not started`: no meaningful implementation found.
4. Build a short implementation plan with validation commands before editing.
5. Implement the smallest coherent slice that advances the selected roadmap item.
6. Run the validation chosen by `.agents/skills/timbregrid-validation`.
7. Update `README.md` roadmap/status only when the implemented behavior and validation justify it.
8. Final response should name the roadmap item advanced, files changed, and validations run.

## Roadmap Update Rules

- Keep partial labels when important work remains.
- Do not mark a model adapter, registry path, benchmark path, or provenance path complete from docs-only work.
- If generated files need updates, run the generator rather than hand-editing generated output.
- If the selected item changes project direction, document that in README before claiming completion.
