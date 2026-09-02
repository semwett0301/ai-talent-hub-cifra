# AI Analytical Center (Cifra Hackathon)

An AI-powered intelligence hub that automatically **collects, structures, and
summarizes industry news** in a single interface, with full user control over
sources and content.

Built for PR/GR teams who otherwise spend 3–4 hours a day manually monitoring
media, regulators, and Telegram channels.

## What it does

- **Collect** publications from media (RSS), regulator websites, and Telegram.
- **Summarize** with an LLM: short summary, key entities, category, priority.
- **Dashboard** with filtering and search, linking to the original.
- **User control**: add/edit/delete sources; edit or hide articles; add items
  manually.

## Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`.
Types: `feat`, `fix`, `chore`, `refactor` (also `docs`, `test`, `perf`, `style`).
Branch + PR rather than committing to `main`. Full rules in
`.claude/rules/20-git.md`.

## Out of scope (per the brief)

Production-scale load, additional modalities, and information security.
