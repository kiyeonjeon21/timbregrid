# Claude Code Instructions

This project's agent guidance lives in [`AGENTS.md`](./AGENTS.md). Treat it as
the single source of truth for project workflow, validation, and public-repo
hygiene. Do not duplicate that content here.

When `AGENTS.md` references `.agents/skills/*` (e.g. `timbregrid-roadmap`,
`timbregrid-oss-review`, `timbregrid-validation`), read those skill files
directly from disk on demand instead of expecting them to auto-load. They are
shared with the Codex setup and should stay in `.agents/skills/` as the
canonical location.

`.codex/` is Codex-specific (its own config schema and hooks). Ignore it.
