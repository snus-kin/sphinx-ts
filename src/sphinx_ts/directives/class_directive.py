"""TypeScript Class Auto-Directive Module.

Contains the TSAutoClassDirective class for auto-documenting TypeScript classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes
from docutils.statemachine import StringList
from sphinx import addnodes
from sphinx.util import logging

from .base import TSAutoDirective

if TYPE_CHECKING:
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

        # Register only main class in TOC, not every method and property

        # Create the main class descriptor with proper docutils structure
        class_desc = addnodes.desc(domain="ts", objtype="class")

        # Create class signature
        class_sig = addnodes.desc_signature("", "", first=True)
        class_sig["class"] = "sig-object ts"
        class_sig["ids"] = [f"class-{class_name}"]
        class_sig += addnodes.desc_annotation("", "class ")
        class_sig += addnodes.desc_name("", class_name)
        class_desc += class_sig

        # Create class content container
        class_content = addnodes.desc_content()
        class_desc += class_content

        # Add class description
        if ts_class.doc_comment:
            try:
                # Format the doc comment as RST and parse it into proper nodes
                formatted_rst_lines = self.format_doc_comment(
                    ts_class.doc_comment
                )
                if formatted_rst_lines:
                    # Use Sphinx's content parsing mechanism
                    content = StringList(formatted_rst_lines)
                    node = nodes.Element()
                    self.state.nested_parse(content, self.content_offset, node)

                    # Add the parsed content to class content
                    for child in node.children:
                        class_content.append(child)

            except Exception as e:
                # Fallback to plain text if RST parsing fails
                logger.warning(
                    "Failed to parse RST content for class %s: %s",
                    class_name,
                    e,
                )
                desc_para = nodes.paragraph()
                desc_para.append(nodes.Text(ts_class.doc_comment.description))
                class_content.append(desc_para)

        # Store class name for later use with methods and properties
        self.current_class_name = class_name

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
