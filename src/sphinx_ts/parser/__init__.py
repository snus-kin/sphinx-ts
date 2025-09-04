"""TypeScript Parser Package.

Provides classes and utilities for parsing TypeScript files and extracting
documentation information.
"""

from .ast_nodes import (
    TSClass,
    TSEnum,
    TSEnumMember,
    TSInterface,
    TSMember,
    TSMethod,
    TSProperty,
    TSVariable,
)
from .doc_comment import TSDocComment
from .mixins import NamedObjectMixin
from .ts_parser import TSParser
from .value_parser import TSValueParser

__all__ = [
    "NamedObjectMixin",
    "TSClass",
    "TSDocComment",
    "TSEnum",
    "TSEnumMember",
    "TSInterface",
    "TSMember",
    "TSMethod",
    "TSParser",
    "TSProperty",
    "TSValueParser",
    "TSVariable",
]
