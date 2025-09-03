"""TypeScript Auto-Directives Package.

Provides auto-documentation directives for TypeScript code similar to autodoc.
"""

from .base import TSAutoDirective
from .class_directive import TSAutoClassDirective
from .data_directive import TSAutoDataDirective
from .enum_directive import TSAutoEnumDirective
from .interface_directive import TSAutoInterfaceDirective

__all__ = [
    "TSAutoClassDirective",
    "TSAutoDataDirective",
    "TSAutoDirective",
    "TSAutoEnumDirective",
    "TSAutoInterfaceDirective",
]
