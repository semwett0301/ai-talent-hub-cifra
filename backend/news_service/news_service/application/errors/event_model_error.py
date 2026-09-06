"""Failure raised when event-model setup or inference cannot complete."""


class EventModelError(RuntimeError):
    """An event LLM call failed or returned an invalid structured response."""
