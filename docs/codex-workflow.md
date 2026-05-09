# Codex Project Workflow

This repository keeps Codex customization in project scope so future sessions can continue from the same roadmap and validation rules.

## Files

| Path | Purpose |
|---|---|
| `AGENTS.md` | Durable repo instructions that Codex should read before work starts. Keep this short and operational. |
| `.agents/skills/timbregrid-roadmap/SKILL.md` | Repeatable workflow for README roadmap planning and milestone continuation. |
| `.agents/skills/timbregrid-validation/SKILL.md` | Repeatable workflow for choosing the right validation commands by changed area. |
| `.codex/config.toml` | Project-scoped Codex feature and agent limits. |
| `.codex/agents/*.toml` | Project custom agents for explicit subagent workflows. |
| `.codex/hooks.json` and `.codex/hooks/` | Advisory lifecycle hooks for session context and roadmap hygiene reminders. |

## Operating Model

1. README remains the product and roadmap source of truth.
2. `AGENTS.md` says how Codex should operate in this repo.
3. Skills hold longer repeatable procedures so `AGENTS.md` does not become a large playbook.
4. Custom agents are available for explicit parallel work, but normal implementation should stay single-agent unless delegation has a clear payoff.
5. Hooks are reminders, not the main enforcement mechanism. Tests, CLI checks, generated-file checks, and CI should enforce correctness.

## Roadmap Discipline

When continuing work from README:

1. Read `Current MVP Scope`, `Development Roadmap`, `First Milestone`, and `Next Milestones`.
2. Pick the first relevant unfinished item.
3. Implement the smallest coherent slice.
4. Run validation from the validation skill.
5. Update README status only after the behavior is implemented and validated.

## Subagent Use

Use project custom agents only when the user asks for subagents or parallel agent work.

- `roadmap_planner`: maps README roadmap state to a next implementable plan.
- `reviewer`: checks correctness, generated artifact drift, missing tests, and roadmap accuracy.
- `registry_guard`: focuses on manifests, schemas, registry output, support matrix, and benchmark examples.

## Maintenance

- Add to `AGENTS.md` only when a rule should apply to nearly every future Codex session.
- Add or edit a skill when a repeatable workflow needs more detail than belongs in `AGENTS.md`.
- Add hooks only for lightweight reminders or context injection.
- Do not commit secrets, personal tokens, local auth files, or user-specific `~/.codex` state.
