"""Domain schemas — DB-backed data shapes (SQLAlchemy ORM).

Plain in-memory shapes (no DB involvement) live in `../entities/` instead.
"""

from domain.schemas.news import News
from domain.schemas.npa import Npa
from domain.schemas.source import Source

__all__ = ["News", "Npa", "Source"]
