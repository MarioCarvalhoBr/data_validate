# ADR-0012: Multi-agent development workflow (orchestrator + specialised subagents) governed by `.claude/rules/`

- Status: Accepted
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

This migration is large by construction: 89 backlog items across bugs, security, architecture,
testing, performance, tooling and docs (`.specs/quality/backlog/README.md`), executed over five
phases (`08-migration-roadmap.md`) that touch nearly every file in `data_validate/` and `tests/`
while keeping the live CLI/report/JSON contract green throughout (ADR-0002). Before this execution
there was no written policy for how AI-assisted changes to this repository should be structured:
no rules directory, no distinction between "read and plan" and "write code" responsibilities, and
no standing convention for which model tier should perform which class of task. Left unconstrained,
a single high-power model performing every task — from renaming a variable to designing the
`SheetSpec` registry (ADR-0003) — is both slower and more expensive than necessary, and gives no
separation between the agent that writes a change and the agent that reviews it, which the
project's own Clean Code standard already implicitly expects ("Boy Scout Rule", the emphasis on
tests as the mechanism that "enable[s] refactoring", per `.github/copilot-instructions.md`).
SEC-006's documented 2026-08-25 incident — a legacy pre-commit hook silently expanding a 9-file
docs commit into 22 files — is itself evidence of what happens when automated tooling acts without
a written, reviewable contract for what it is allowed to touch.

## Decision

Adopt the model-delegation policy defined verbatim in `.claude/rules/model-delegation.md` (also
reproduced in the master prompt governing this execution): the main session (a high-power model)
acts strictly as an **orchestrator** — it delegates, provides context, and reviews — and
participates directly in coding only when a case is genuinely complex enough to need the top model
(subtle debugging, architecture decisions). Routine implementation work (new features, refactors,
bug fixes with a known cause) is delegated to `sonnet`-tier subagents via the `Agent` tool; trivial,
mechanical changes (renames, copy tweaks, small config edits, running validations) go to
`haiku`-tier subagents. `.claude/agents/` defines twelve specialised roles, each with an explicit
model tier, tool allowlist, and a `Never do` boundary: `implementer` (sonnet, TDD implementation),
`test-engineer` (sonnet, coverage expansion), `code-reviewer` (sonnet, no `Edit`/`Write` — findings
only), `security-auditor` (sonnet, threat-model-driven review), `integration-tester` (sonnet, golden
harness), `performance-engineer` (sonnet, profiling), `spec-writer` (sonnet, keeps `.specs/`/ADRs/
rules synchronised with code), `i18n-guardian` (haiku, catalog parity), `docs-writer` (haiku, root
docs from code — never invents behaviour), `protocol-expert` (opus, protocol-vs-implementation
divergence), `migration-architect` (opus, ADRs and interface design, does not implement), and
`release-manager` (haiku, versioning/changelog). Every subagent is briefed with the relevant files,
the applicable `.claude/rules/`, and the spec-sync requirement, and its output is reviewed in the
main session before being considered done. Every change that alters behaviour, a business rule, the
CLI contract, file layout, or a convention must update the corresponding spec in the same commit
(`.claude/rules/spec-sync.md`); the `stop-check.sh` hook alerts (without blocking) when
`data_validate/` changes without a corresponding `.specs/` touch.

## Consequences

### Positive
- Cost and latency scale with task complexity: mechanical work runs on `haiku`, routine
  implementation on `sonnet`, and the top-tier model is reserved for genuine architecture/debugging
  judgement calls (like the ADRs in this very set) — the standing instruction in
  `model-delegation.md` makes this the default, not an ad hoc choice per task.
- Review is structurally separated from authorship: `code-reviewer` and `security-auditor` have no
  write access, so a subagent cannot both introduce and approve its own change.
- Specialisation improves output quality per task: `protocol-expert` (opus) is the one role that
  needs deep, sustained familiarity with the 1.13 protocol PDF and business-rules specs, while
  `docs-writer` (haiku) is explicitly forbidden from inventing behaviour — it must read the code.

### Negative
- Coordinating many subagents adds orchestration overhead (briefing each with sufficient context,
  reviewing each output) compared to one continuous session; accepted because the alternative —
  one model doing everything — has already proven, in this same repository (SEC-006), that
  unreviewed automated changes at scale are a real risk, not a hypothetical one.
- The policy depends on the orchestrator consistently choosing the *right* tier and *not* skipping
  the review step under time pressure; `.claude/rules/model-delegation.md` frames delegation as a
  standing instruction precisely so it isn't treated as optional per task.

## Alternatives considered

### Single-agent monolithic session, top-power model performs all work directly
Rejected: this is strictly more expensive and slower for the volume of routine work in an 89-item
backlog, and removes the authorship/review separation that catches mistakes before they land —
exactly the gap SEC-006's incident exposed when no reviewing party existed for what a hook did.

### Fully autonomous multi-agent swarm with no human-authored rules files
Rejected: without `.claude/rules/` as a written, version-controlled contract, agent behaviour is
not reproducible across sessions and there is no artefact a human reviewer (or another subagent)
can check a change against — the whole point of ADR-0001 (recording decisions) and spec-sync
(keeping specs/code aligned) is defeated if the agents' own operating rules aren't equally durable
and inspectable.

### CI-bot-only automation (scripted, no interactive orchestrator making judgement calls)
Rejected: several of this migration's decisions — the `SheetSpec` design (ADR-0003), the CLI
contract (ADR-0005), and the ADRs in this set generally — require judgement about trade-offs that a
scripted bot cannot make; the workflow instead reserves those calls for the orchestrator and the
`opus`-tier `migration-architect`, while routing genuinely mechanical work to cheaper automation.

## Links

- Backlog: `.specs/quality/backlog/08-migration-roadmap.md` ("Working agreement per item");
  `SEC-006` (`02-security.md`, motivating evidence)
- Specs: `.claude/rules/model-delegation.md`, `.claude/rules/spec-sync.md`, `.claude/agents/`
- Related ADRs: ADR-0001 (the record-keeping this workflow relies on)

---
Last synced with code: a4f76c7
