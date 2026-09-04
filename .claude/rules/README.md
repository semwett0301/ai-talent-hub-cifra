# Project rules

Project-specific rules for Claude Code — hard constraints and conventions the
agent must follow when working in this repo. Skills (`.claude/skills/`) teach
*how* to use a technology; rules encode *what this project requires*.

## How to write a rule

One concern per file, `NN-topic.md`, kept short and imperative:

```markdown
# <Rule title>

- Do X.
- Never Y.
- When Z, prefer A over B (because ...).
```

Keep rules actionable and testable. Remove a rule once it's obsolete rather than
letting it rot. Reference `CLAUDE.md` for the architectural overview; put
enforceable specifics here.

## Files

- `00-conventions.md` — baseline conventions.
- `10-core.md` — core development principles.
- `20-git.md` — commit conventions.
- `30-python.md` — Python guidelines.
- `40-monorepo.md` — repo structure, backend/frontend split, networking.
- `50-docs.md` — keep each folder's `README.md` current.
- `60-logging.md` — log every logical action; keep library noise capped.
