# Use cases

## Actors

| Actor | Description |
|---|---|
| Sector analyst | Prepares the spreadsheet bundle for one sector and needs to know exactly what to fix |
| Canoa platform | Automated ingestion; runs the validator on upload and parses the JSON summary and report path |
| INPE maintainer | Develops rules, keeps the tool aligned with the protocol |
| Researcher / integrator | Uses the validator as a library or in a CI pipeline for their own datasets |

## Index

| ID | Title | Primary actor | Status |
|---|---|---|---|
| [UC-01](UC-01-validate-bundle.md) | Validate a bundle from the command line | Sector analyst | supported |
| [UC-02](UC-02-generate-report.md) | Generate and read the validation report | Sector analyst, platform | supported (PDF optional in target) |
| [UC-03](UC-03-ci-batch-validation.md) | Validate many bundles in batch / CI | Platform, maintainer | partially (shell scripts) → `tools/harness/run_fixtures.py` |
| [UC-04](UC-04-library-usage.md) | Use the validator as a Python library | Researcher / integrator | target (Phase 1) |
| [UC-05](UC-05-add-new-rule.md) | Add a new validation rule | INPE maintainer | supported via skill `validation-rule-authoring` |

Each use case follows `../templates/use-case.md`: goal, preconditions, main flow, alternative
flows, postconditions, related rules/backlog.

Last synced with code: 09279f4
