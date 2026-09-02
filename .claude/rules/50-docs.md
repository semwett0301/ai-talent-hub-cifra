# Folder documentation

Every folder has a small `README.md` — a quick hint for Claude/devs, not
exhaustive docs. Keep it short. Two things:

- **File map** — each file / subfolder on one line: what functionality it holds.
- **Notes** — a couple of implementation specifics or local conventions common to
  the package that are worth knowing (patterns, gotchas). Skip if there's nothing
  notable — don't pad.

When you add, remove, rename, or meaningfully change files in a folder, update its
`README.md` in the same change (a stale map is a bug). Generated/ignored dirs
(`node_modules`, `dist`, `.venv`, `__pycache__`, caches) are exempt.
