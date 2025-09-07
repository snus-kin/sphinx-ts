"""TypeScript Class Auto-Directive Module.

Contains the TSAutoClassDirective class for auto-documenting TypeScript classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.util import logging

from .base import TSAutoDirective

if TYPE_CHECKING:
    from docutils import nodes

    from sphinx_ts.parser import TSClass

logger = logging.getLogger(__name__)


class TSAutoClassDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript classes."""

    def run(self) -> list[nodes.Node]:
        """Run the directive."""
        class_name = self.arguments[0]

        return self._process_class(class_name)

    def _process_class(self, class_name: str) -> list[nodes.Node]:
        """Process a TypeScript class."""
        # Find and register the class using common processing pattern
        result = self._process_object_common(class_name, "class")
        if not result:
            return []

        ts_class: TSClass = result["object"]

        # Register methods and properties with domain
        self._register_members_with_domain(
            class_name, methods=ts_class.methods, properties=ts_class.properties
        )

        # Create standardized class descriptor
        class_desc, class_sig, class_content = self._create_standard_desc_node(
            "class", class_name
        )

        # Create standardized signature
        self._create_standard_signature(class_sig, class_name, "class")

        # Add standardized documentation content
        self._add_standard_doc_content(class_content, ts_class.doc_comment)

        # Add constructor if present
        if ts_class.constructor:
            constructor_desc = self._format_method_common(
                ts_class.constructor, class_name, "Constructor"
            )
            if constructor_desc:
                class_content.append(constructor_desc)

        # Add properties directly to class content (after constructor)
        if ts_class.properties:
            for prop in ts_class.properties:
                prop_desc = self._format_property_common(prop, class_name)
                if prop_desc:
                    class_content.append(prop_desc)

        # Add methods directly to class content (after properties)
        if ts_class.methods:
            for method in ts_class.methods:
                method_desc = self._format_method_common(method, class_name)
                if method_desc:
                    class_content.append(method_desc)

        return [class_desc]
