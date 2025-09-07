"""TypeScript Interface Auto-Directive Module.

Contains the TSAutoInterfaceDirective class for auto-documenting interfaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.util import logging

from .base import TSAutoDirective

if TYPE_CHECKING:
    from docutils import nodes

    from sphinx_ts.parser import TSInterface

logger = logging.getLogger(__name__)


class TSAutoInterfaceDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript interfaces."""

    def run(self) -> list[nodes.Node]:
        """Run the interface auto-documentation directive."""
        interface_name = self.arguments[0]
        return self._process_interface(interface_name)

    def _process_interface(self, interface_name: str) -> list[nodes.Node]:
        """Process a TypeScript interface."""
        # Find and register the interface using common processing pattern
        result = self._process_object_common(interface_name, "interface")
        if not result:
            return []

        ts_interface: TSInterface = result["object"]

        # Register methods and properties with domain
        self._register_members_with_domain(
            interface_name,
            methods=ts_interface.methods,
            properties=ts_interface.properties,
        )

        # Create standardized interface descriptor
        interface_desc, interface_sig, interface_content = (
            self._create_standard_desc_node("interface", interface_name)
        )

        # Create standardized signature with type parameters and extends
        self._create_standard_signature(
            interface_sig,
            interface_name,
            "interface",
            type_params=ts_interface.type_parameters,
            extends=ts_interface.extends,
        )

        # Add standardized documentation content
        self._add_standard_doc_content(
            interface_content, ts_interface.doc_comment
        )

        # Add properties directly to interface content (before methods)
        if ts_interface.properties:
            for prop in ts_interface.properties:
                prop_desc = self._format_property_common(prop, interface_name)
                if prop_desc:
                    interface_content.append(prop_desc)

        # Add methods directly to interface content (after properties)
        if ts_interface.methods:
            for method in ts_interface.methods:
                method_desc = self._format_method_common(method, interface_name)
                if method_desc:
                    interface_content.append(method_desc)

        return [interface_desc]
