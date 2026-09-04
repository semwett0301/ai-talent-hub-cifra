---
name: swarm
description: Dispatch independent, bounded work items to Codex subagents in parallel and consolidate their results. Use when items can be handled independently; do not use for sequential or tightly coupled work.
---

# Parallel work with Codex subagents

Use Codex's collaboration tools to process a collection of independent work
items. One subagent handles one clear unit of work and reports a concise,
structured result. The primary agent remains responsible for synthesis,
validation, and any final change.

## When to use it

Use this skill when the requested work has independent items, such as reviewing
separate files, classifying records, or researching unrelated questions.

Do not use it when later steps depend on earlier results, when the task is small
enough to complete directly, or when the work changes overlapping files.

## Dispatch

1. Read or derive the full list of items first. Define stable item IDs and the
   expected result fields.
2. Give every subagent a self-contained instruction: its exact item, scope,
   constraints, output format, and any relevant file paths. Do not assume a
   subagent remembers a previous call.
3. Spawn only as many agents as the available concurrency permits. As agents
   finish, dispatch the next queued item. Keep file-writing work partitioned so
   no two agents edit the same target.
4. Collect every report, identify failures or omissions, and retry only those
   specific items when a retry is justified.
5. Validate the consolidated result yourself before presenting or applying it.

## Result format

Ask each subagent to return this shape whenever practical:

```text
item_id: <stable identifier>
status: completed | failed | blocked
result: <requested structured answer>
evidence: <files, commands, or sources used>
notes: <limitations or follow-up needed>
```

## Practical constraints

- Prefer direct work for fewer than three small items; coordination can cost
  more than the work itself.
- Do not parallelize destructive operations, external messages, or edits to a
  shared file without a clear non-overlapping partition.
- Preserve the user's authorization boundaries. A subagent may inspect and
  report, but only perform external or destructive actions that the user has
  authorized for the overall task.
- Treat subagent conclusions as evidence, not as a final answer. Reconcile
  disagreements against the source material.
