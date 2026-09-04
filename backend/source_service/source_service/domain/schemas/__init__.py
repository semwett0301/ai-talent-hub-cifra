"""Domain schemas — DB-backed data shapes (SQLAlchemy ORM).

Plain in-memory shapes (no DB involvement) live in `../entities/` instead.
"""

from source_service.domain.schemas.source import Source

__all__ = ["Source"]
