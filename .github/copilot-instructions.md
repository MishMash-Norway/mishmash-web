# Copilot instructions

Follow [AGENTS.md](../AGENTS.md) at the repository root. It is the brief for every agent working on mishmash.no: how to work, the language rules (English source, Bokmål mirror by hand, Nynorsk generated), the writing rules, the files never to edit by hand and the checks to run. The detail is in [CONTENT_HANDOVER.yml](../CONTENT_HANDOVER.yml).

The rules most often missed:

- Edit the English page and its Bokmål mirror under `site/no/` in the same change. Never edit `site/nn-auto/`.
- British English; no em dash and no spaced dash; no bold inside a sentence; KI, not AI, in Norwegian.
- Public text names no person as the author of a decision.
- Pull before working and before pushing; the nightly sync and other people push to `main`.
- Ask before deleting, publishing a draft or anything outside the repository.
