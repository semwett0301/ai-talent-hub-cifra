"""Definitions of the shared batch consumer — the config it takes and the port it calls.

Pure declarations, no I/O: a service imports these to configure the consumer and to
implement the handler it feeds.
"""

from domain.core.rabbit.model.config import BatchConsumerConfig
from domain.core.rabbit.model.handler import BatchHandler

__all__ = ["BatchConsumerConfig", "BatchHandler"]
