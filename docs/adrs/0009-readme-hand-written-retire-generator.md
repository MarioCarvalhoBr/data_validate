# ADR-0009: README maintained by hand; retire the template generator

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`data_validate/helpers/tools/readme/generate_readme.py` builds the repository's `README.md` from
`data_validate/static/templates/README.TEMPLATE.md` at build/publish time. The module has an
import-time side effect — `print(f"{METADATA.__welcome__}\n")` at line 7, executed merely by
importing the module, before `generate_readme()` is even called — and a second print at line 23
announcing the target repo/version. `generate_readme()` (lines 28-59) reads the template, replaces
two placeholders (`content.replace("{{USER_REPO}}", USER_REPO).replace("{{REPO_VERSION}}",
REPO_VERSION)`, line 44) sourced from `METADATA.__version__`/`METADATA.__status__`
(`config/metadata_info.py`), and writes the result to `README.md` at the repository root (`
OUTPUT_FILE = Path(__file__).resolve().parents[4] / "README.md"`, line 25). This script lives
**inside the shipped package** (`data_validate/helpers/tools/readme/`), which ARC-010 already flags
as "package layout mixes tooling, demos and runtime" — a build-time documentation generator has no
business being importable at runtime by anything that depends on `canoa_data_validate`. It is
explicitly excluded from coverage measurement (`pyproject.toml`, `[tool.coverage.run] omit`
includes `"generate_readme.py"`), meaning it is untested code that writes to the repository root.
The `Makefile` wires it to two targets: `readme: ## Generate README documentation` (lines 86-87,
`$(PYTHON) $(PATH_SRC)/helpers/tools/readme/generate_readme.py`) and `publish: readme` (line 35),
so every package publish first regenerates `README.md` from the template as a side effect of
building a wheel — a documentation-authoring step hidden inside a release step. DOC-001 separately
notes the *current* generated `README.md` is 27 kB with a hard-coded badge version, itself evidence
that template-generated prose drifts from what a human would actually want reviewers to read in a
PR diff.

## Decision

Retire the generator. `README.md` becomes hand-written prose (rewritten from scratch per
`README.md`'s new structure — see the project's docs plan), edited directly in PRs like any other
document, with version references coming from the PyPI/CI badge (shields.io, reading the published
package's latest version) rather than a baked-in `{{REPO_VERSION}}` string that requires a build
step to stay current. `data_validate/helpers/tools/readme/generate_readme.py` and
`data_validate/static/templates/README.TEMPLATE.md` are deleted in Phase 5 under ARC-010's package-
layout cleanup (not immediately, to avoid breaking `make publish` mid-migration before the release
workflow, ADR-0010, is in place); the Makefile's `readme` target and `publish`'s dependency on it
are removed **now**, in this execution, since `publish` itself is being replaced by the CI
`release.yml` workflow (`08-migration-roadmap.md` §6.3) which does not invoke a README generator.

## Consequences

### Positive
- `README.md` diffs in PRs show exactly the prose change being proposed, instead of a full
  27 kB regeneration with every placeholder substitution re-applied.
- Removes an untested, import-time-side-effecting script from the shipped package
  (`canoa_data_validate` no longer imports a documentation build tool at runtime), directly
  addressing the ARC-010 "tooling mixed with runtime" smell for this specific case.
- One less moving part in the release process: publishing no longer depends on a template-
  substitution step succeeding.

### Negative
- Version mentions inside README prose (if any) must be updated by hand or phrased in a way that
  doesn't need updating (e.g. "see the latest release on PyPI" instead of a literal version
  string) — a small ongoing discipline cost, mitigated by relying on badges for anything that
  changes per release.
- Until Phase 5 physically deletes the files, `generate_readme.py` and `README.TEMPLATE.md` remain
  in the tree unused by any Make target — a temporary, clearly-dead artifact accepted as the cost
  of not breaking anything mid-migration; tracked so Phase 5 doesn't forget to remove it.

## Alternatives considered

### Keep the generator, but fix its side effects (remove import-time `print`, cover it with tests)
Rejected: fixing the symptoms leaves the underlying question unanswered — does templating actually
earn its cost for a document that changes rarely and is reviewed by humans? A generated README
still requires contributors to edit the *template* and remember to regenerate, an extra step for
no benefit once the only two placeholders (`USER_REPO`, `REPO_VERSION`) are removed from prose in
favour of badges.

### Move the generator to `tools/` as opt-in documentation tooling, keep templating
Rejected: this still requires the same placeholder scheme and the same "remember to regenerate
before every release" discipline; a hand-written README is simpler to review and simpler to keep
correct than a template-plus-generator pair solving a problem (two placeholders) that badges solve
more directly and automatically.

### Template with Jinja2, add a CI job that fails if `README.md` is stale versus the template
Rejected: this adds CI complexity (a staleness check, template rendering in CI) to guard against a
class of drift that a hand-written README with badge-sourced version info doesn't have in the
first place — solving a self-inflicted problem rather than removing its cause.

## Links

- Backlog: `ARC-010` (`03-architecture.md`); `DOC-001` (`07-docs-i18n.md`);
  `08-migration-roadmap.md` Phase 5 (package layout cleanup)
- Specs: `.specs/architecture/target-architecture.md` (module map:
  `helpers/tools/readme/generate_readme.py` → "deleted, ADR-0009")
- Related ADRs: ADR-0003 (both retire duplicated, generator-adjacent metadata)

---
Last synced with code: a4f76c7
