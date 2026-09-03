"""Declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base; every service's models inherit from it."""
