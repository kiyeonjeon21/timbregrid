---
name: timbregrid-oss-review
description: Use when reviewing TimbreGrid's OSS value, public-release readiness, repository positioning, README claims, contributor funnel, or whether the project is useful before more roadmap work lands.
---

# TimbreGrid OSS Review Workflow

Use this skill when the task mentions OSS value, public release, public readiness, repository positioning, README claim review, contributor readiness, or whether TimbreGrid is worth publishing.

## Inputs

- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `docs/support-matrix.md`
- `docs/benchmarking.md`
- `docs/benchmark-submissions.md`
- `docs/conformance.md`
- `.github/workflows/ci.yml`
- `.github/ISSUE_TEMPLATE/*`
- `pyproject.toml`
- Relevant source files for claims being reviewed

## Review Axes

1. OSS value proposition:
   - Identify who benefits today: users, adapter authors, benchmark contributors, integration authors, or maintainers.
   - Classify the current value as runtime, evaluation, registry, conformance, routing, integration, or documentation value.
   - Separate value that exists today from value that depends on roadmap items.
2. Claim safety:
   - Check that README claims match implemented behavior.
   - Ensure manifest-only models, fake benchmark data, optional adapters, and missing features are clearly labeled.
   - Flag wording that implies real hardware performance, broad OpenAI compatibility, or executable model support without evidence.
3. Contributor readiness:
   - Check whether contributors can submit manifests, benchmarks, conformance improvements, and adapters with clear validation commands.
   - Prefer improvements that unblock external contributions before adding broad feature scope.
4. Trust surface:
   - Check CI coverage, license clarity, security guidance, issue templates, PR template, and public-data hygiene.
   - Flag private data, secrets, local-only paths, or claims that should not be in public docs.
5. Next highest-value OSS work:
   - Prefer real benchmark artifacts, benchmark submission validation, one small real adapter, OpenAI SDK examples, and integration examples.
   - Keep roadmap recommendations conservative and evidence-based.

## Output

Lead with findings when reviewing. Include:

- Verdict: `publish now`, `publish with caveats`, or `not ready`.
- Current OSS value and primary audience.
- Top risks or claim gaps, ordered by severity with file references.
- Concrete next work that most improves public value.
- README or docs wording changes only when claims are stale, overstated, or unclear.

## Rules

- Do not mark roadmap work complete from docs-only review.
- Do not recommend publishing real benchmark claims without raw benchmark JSON evidence.
- Do not treat Codex hooks or skills as public product value unless the user is specifically reviewing project automation.
- Keep public README advice concise; move detailed contribution, benchmark, and conformance guidance into dedicated docs.
