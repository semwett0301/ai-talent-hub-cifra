# Service domain layer

A service that reasons about its own entities keeps them in `<service>/<service>/domain/`
— its **own** domain layer. The shared kernel (`backend/common`) holds only what crosses
service boundaries (`NewsDTO`, ORM schemas, settings); never put a service-local entity
there.

## What goes where

- **Domain answers "what"**: what an entity is, what state it is in, what counts (a fresh
  date, an article-like link). Pure: no I/O, no ports, no library clients, no knowledge of
  the pipeline order.
- **Application answers "how"**: how a value is obtained (parsing a printed date, the
  HTML/LLM techniques that extract it), in which order steps run, how strict to be
  (thresholds, budgets). A vocabulary of *techniques* (e.g. `DateSource`) is application,
  even if the domain stores the resulting label.
- A pure function that would not change if the crawler library or the pipeline order
  changed is domain; one that names a technique or a library is application.

## Layout — one entity per subpackage

```
domain/
  <entity>/
    <entity>.py     # the entity itself — the only module at the root
    model/          # what it is made of: sub-models, value objects, its enums
    rules/          # what judges it: scoring rules, windows, invariants
  <mechanism>/      # shared machinery only (e.g. scoring/): model/ + the mechanism
  <topic>.py        # cross-entity identity rules (e.g. urls.py)
```

- The entity module is the **only** file at the root of its package; everything else is in
  `model/` or `rules/`. Each subpackage re-exports its public API from `__init__.py` and
  has its own `README.md` (rule `50-docs`).
- **Entity-specific things live with the entity.** A rule, a vocabulary, a regex that is
  about articles goes to `article/rules`; about hubs, to `hub/rules`. Only what is about
  *neither* — the generic `RuleScorer`, terms both sides read — may sit in a shared
  package, and its README must say so.
- Entities are **immutable**: a step returns a copy one stage further (`with_x(...)`,
  `accept()`, `reject(reason)`); a terminal method guards its invariants and raises.
- Derived values are **computed, never stored**: no `score` field on an entity — call the
  scorer where the number is needed.
- **Thresholds are the use case's.** The domain says how article-like (`Score`), the use
  case decides `>= 0.18`. Keep the constant next to the code that applies it.
