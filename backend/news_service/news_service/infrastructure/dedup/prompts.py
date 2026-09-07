"""Prompts retained from the supplied precision-first dedup pipeline."""

PRIMARY_EVENT_SYSTEM = """
You extract the PRIMARY news event from one article, tweet, or post, and write one
EVENT SUMMARY for it. The downstream task is high-precision cross-document event
identity, so be conservative.

Rules:
1. PRIMARY means the occurrence that makes this item newsworthy now. Historical and background
   events are not primary.
2. Use only facts supported by the supplied title, text, and metadata. Never infer or fill gaps
   from world knowledge.
3. A relative date may be resolved only from the supplied publication time.
4. Follow-up actions are distinct occurrences: signing and regulatory approval are not one event.
5. Shared topic, actor, object, or storyline never implies the same event.
6. If the item has no concrete event, set primary_event_found=false and return exactly
   "No concrete primary event identified." as the summary.
7. Otherwise the summary is one short, neutral, self-contained sentence. It will be embedded to
   find candidates, so retain explicitly supported identity-bearing details: actor, action,
   object, location, time, lifecycle stage, identifiers, and quantities.
8. Preserve the source language where possible. Do not add labels, commentary, uncertainty
   explanations, or source metadata.
9. Announcement, signing, approval, launch, outage, resumption, and completion are distinct
   occurrences unless the evidence clearly says otherwise.
"""

PRECLUSTER_ALIGNMENT_SYSTEM = """
You receive trusted anchor event summaries and candidate summaries retrieved by vector similarity.
Return exactly one member_decisions entry for every candidate news_id.

Decision rules:
- SAME requires positive evidence for the same concrete occurrence and no hard conflict. Normally
  require two compatible identity signals among actor, action, object, named location, lifecycle
  stage, identifier, distinctive quantity, and event time.
- DIFFERENT means noise, a follow-up, subevent, contradictory occurrence, or distinct lifecycle
  stage.
- UNCERTAIN means available facts cannot distinguish this candidate from another plausible event.

An omitted detail is not a conflict. Put only identity-blocking missing facts in critical_unknowns.
Put true contradictions in hard_conflicts. Keep every verdict candidate-specific: one candidate's
conflict must never affect another candidate. Shared topic, actors, or wording alone are not proof.
"""
