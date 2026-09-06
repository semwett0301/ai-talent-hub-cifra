# state

State-pattern behavior for daily tracking. `tracking.py` allows checks and moves to
`published.py` after publication; both terminal states reject further checks. `factory.py`
maps the persisted enum to behavior without leaking conditionals into orchestration.
