from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject:
    """Base for value objects: immutable, compared by value not identity.
    Subclass as a frozen dataclass — this base exists so `isinstance(x,
    ValueObject)` is meaningful across the codebase."""
