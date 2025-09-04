"""TypeScript Interface Auto-Directive Module.

Contains the TSAutoInterfaceDirective class for auto-documenting interfaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging

from .base import TSAutoDirective

if TYPE_CHECKING:
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

        # Create the main interface descriptor with proper docutils structure
        interface_desc = addnodes.desc(domain="ts", objtype="interface")

        # Create interface signature
        interface_sig = addnodes.desc_signature("", "", first=True)
        interface_sig["class"] = "sig-object ts"
        interface_sig["ids"] = [f"interface-{interface_name}"]
        interface_sig += addnodes.desc_annotation("", "interface ")
        interface_sig += addnodes.desc_name("", interface_name)

        # Add type parameters if present
        if ts_interface.type_parameters:
            interface_sig += nodes.Text(
                f"<{', '.join(ts_interface.type_parameters)}>"
            )

        # Add extends clause if present
        if ts_interface.extends:
            interface_sig += nodes.Text(
                f" extends {', '.join(ts_interface.extends)}"
            )

        interface_desc += interface_sig

        # Create interface content container
        interface_content = addnodes.desc_content()
        interface_desc += interface_content

        # Add interface description
        if ts_interface.doc_comment and ts_interface.doc_comment.description:
            desc_para = nodes.paragraph()
            desc_para.append(nodes.Text(ts_interface.doc_comment.description))
            interface_content.append(desc_para)

        # Store interface name for later use with methods and properties
        self.current_interface_name = interface_name

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
