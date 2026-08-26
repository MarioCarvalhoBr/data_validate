# Git workflow

## Branching

- One branch per backlog item: `feat/<ID>-<slug>` for new capability,
  `fix/<ID>-<slug>` for a bug fix, matching the ID from
  `.specs/quality/backlog/`. Don't stack unrelated items on one branch.

## Commits

- Conventional Commits, in English, with a scope and the backlog/rule ID
  in the subject when one applies:
  `fix(rules): BUG-006 avoid list.remove on missing id`
  `feat(loading): ARC-007 add SheetLoader with size limits`
  `docs(specs): sync business-rules/composition.md with COMP-011`
- One logical change per commit; do not bundle an unrelated refactor into a
  bug-fix commit.
- Never `git push`. This session prepares and commits locally; the human
  pushes.
- Never `git add .` or `git add -A`. Always `git add -- <explicit paths>` so an
  accidental/generated file never rides along in a commit.

## Pull requests

- Use `.github/PULL_REQUEST_TEMPLATE.md`: summary, backlog ID(s) closed,
  specs touched, test plan, screenshots of the report if the HTML output
  changed.
- Every PR that changes `data_validate/**` behaviour updates
  `CHANGELOG.md`'s `Unreleased` section in the same PR.

## Never do

- Never push, force-push, or push to `main` directly.
- Never `git add .` / `git add -A`. Always `git add -- <explicit paths>`.
- Never amend a commit that has already been reviewed or discussed as a
  fixed point — add a new commit instead unless the user explicitly asks
  for an amend.
- Never rewrite history on a shared branch.
