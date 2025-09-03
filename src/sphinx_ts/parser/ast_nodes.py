"""TypeScript AST Node Classes.

Contains all the TypeScript AST node classes representing different
TypeScript constructs like classes, interfaces, methods, properties, etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .mixins import NamedObjectMixin

if TYPE_CHECKING:
    from .doc_comment import TSDocComment


class TSMember(NamedObjectMixin):
    """Base class for TypeScript members (methods, properties, etc.)."""

    def __init__(self, name: str, kind: str) -> None:
        """Initialize a TypeScript member.

        Args:
            name: The name of the member
            kind: The kind of member (method, property, etc.)

        """
        self.name = name
        self.kind = kind  # 'method', 'property', 'constructor', etc.
        self.modifiers: list[str] = []
        self.type_annotation: str | None = None
        self.doc_comment: TSDocComment | None = None
        self.is_static = False
        self.is_private = False
        self.is_protected = False
        self.is_readonly = False
        self.is_optional = False
        self.is_export = False


class TSMethod(TSMember):
    """Represents a TypeScript method."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript method.

        Args:
            name: The name of the method

        """
        super().__init__(name, "method")
        self.parameters: list[dict[str, Any]] = []
        self.return_type: str | None = None
        self.is_async = False
        self.is_generator = False


class TSProperty(TSMember):
    """Represents a TypeScript property."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript property.

        Args:
            name: The name of the property

        """
        super().__init__(name, "property")
        self.default_value: str | None = None


class TSClass(NamedObjectMixin):
    """Represents a TypeScript class."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript class.

        Args:
            name: The name of the class

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.extends: str | None = None
        self.implements: list[str] = []
        self.type_parameters: list[str] = []
        self.methods: list[TSMethod] = []
        self.properties: list[TSProperty] = []
        self.constructor: TSMethod | None = None
        self.is_abstract = False
        self.is_export = False
        self.modifiers: list[str] = []


class TSInterface(NamedObjectMixin):
    """Represents a TypeScript interface."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript interface.

        Args:
            name: The name of the interface

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.extends: list[str] = []
        self.type_parameters: list[str] = []
        self.methods: list[TSMethod] = []
        self.properties: list[TSProperty] = []
        self.is_export = False


class TSVariable(NamedObjectMixin):
    """Represents a TypeScript variable/constant."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript variable.

        Args:
            name: The name of the variable

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.type_annotation: str | None = None
        self.value: str | None = None
        self.kind = "let"  # 'let', 'const', 'var'
        self.is_export = False


class TSEnumMember(NamedObjectMixin):
    """Represents a TypeScript enum member."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript enum member.

        Args:
            name: The name of the enum member

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.value: str | None = None
        self.computed_value: bool = False


class TSEnum(NamedObjectMixin):
    """Represents a TypeScript enum."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript enum.

        Args:
            name: The name of the enum

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.members: list[TSEnumMember] = []
        self.is_const = False
        self.is_export = False
        self.is_declare = False
