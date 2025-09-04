"""Mixins for TypeScript AST Node Classes.

Contains reusable mixins to eliminate code duplication across AST node classes.
"""

from __future__ import annotations


class NamedObjectMixin:
    """Mixin providing comparison and hashing methods for objects with names.

    This mixin eliminates the duplication of __lt__, __eq__, and __hash__
    methods
    across all TypeScript AST node classes that have a 'name' attribute.
    """

    name: str  # Type hint for the name attribute that classes must have

    def __lt__(self, other: object) -> bool:
        """Support sorting of named objects by name (case-insensitive)."""
        if isinstance(other, self.__class__):
            return self.name.lower() < other.name.lower()
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Support equality comparison by name (case-insensitive)."""
        if isinstance(other, self.__class__):
            return self.name.lower() == other.name.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Support using named objects as dictionary keys."""
        return hash(self.name.lower())
