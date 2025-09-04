"""TypeScript Sphinx Extension.

A Sphinx extension that provides autodoc-like functionality for TypeScript
files using Tree-sitter for parsing.
"""

from typing import Any

from sphinx.application import Sphinx

from .directives import (
    TSAutoClassDirective,
    TSAutoDataDirective,
    TSAutoEnumDirective,
    TSAutoInterfaceDirective,
)
from .domain import TypeScriptDomain


def setup(app: Sphinx) -> dict[str, Any]:
    """Set up the Sphinx extension."""
    # Add the TypeScript domain
    app.add_domain(TypeScriptDomain)

    # Add directives
    app.add_directive("ts:autoclass", TSAutoClassDirective)
    app.add_directive("ts:autointerface", TSAutoInterfaceDirective)
    app.add_directive("ts:autoenum", TSAutoEnumDirective)
    app.add_directive("ts:autodata", TSAutoDataDirective)

    # Add configuration values
    app.add_config_value("sphinx_ts_src_dirs", [], "env", [list])
    app.add_config_value("sphinx_ts_exclude_patterns", [], "env", [list])
    app.add_config_value(
        "sphinx_ts_include_private", default=False, rebuild="env", types=[bool]
    )
    app.add_config_value(
        "sphinx_ts_include_inherited", default=True, rebuild="env", types=[bool]
    )

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


__version__ = "0.1.0"
