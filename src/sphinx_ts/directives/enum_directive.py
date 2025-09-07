"""TypeScript Enum Auto-Directive Module.

Contains the TSAutoEnumDirective class for auto-documenting TypeScript enums.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging

from .base import TSAutoDirective

if TYPE_CHECKING:
    from sphinx_ts.parser import TSEnum, TSEnumMember

logger = logging.getLogger(__name__)


class TSAutoEnumDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript enums."""

    def run(self) -> list[nodes.Node]:
        """Run the directive."""
        enum_name = self.arguments[0]

        return self._process_enum(enum_name)

    def _process_enum(self, enum_name: str) -> list[nodes.Node]:
        """Process a TypeScript enum and generate documentation nodes."""
        # Find and register the enum using common processing pattern
        result = self._process_object_common(
            enum_name,
            "enum",
            f"TypeScript enum '{enum_name}' not found in source files",
        )
        if not result:
            return []

        ts_enum: TSEnum = result["object"]

        # Create the main enum documentation
        return self._create_enum_documentation(ts_enum)

    def _create_enum_documentation(self, ts_enum: TSEnum) -> list[nodes.Node]:
        """Create documentation nodes for an enum."""
        content_nodes = []

        # Add enum header
        self._add_enum_header(ts_enum, content_nodes)

        # Add enum members section
        if ts_enum.members:
            self._add_enum_members_section(ts_enum, content_nodes)

        return content_nodes

    def _add_enum_header(
        self, ts_enum: TSEnum, content_nodes: list[nodes.Node]
    ) -> None:
        """Add the enum header section."""
        # Create standardized enum descriptor
        desc_node, sig_node, desc_content = self._create_standard_desc_node(
            "enum", ts_enum.name
        )

        # Collect modifiers
        modifiers = []
        if ts_enum.is_export:
            modifiers.append("export")
        if ts_enum.is_declare:
            modifiers.append("declare")
        if ts_enum.is_const:
            modifiers.append("const")

        # Create standardized signature with modifiers
        self._create_standard_signature(
            sig_node, ts_enum.name, "enum", modifiers=modifiers
        )

        # Add standardized documentation content
        self._add_standard_doc_content(desc_content, ts_enum.doc_comment)

        content_nodes.append(desc_node)

    def _create_enum_signature(self, ts_enum: TSEnum) -> str:
        """Create the enum signature string."""
        signature_parts = []

        if ts_enum.is_export:
            signature_parts.append("export")

        if ts_enum.is_declare:
            signature_parts.append("declare")

        if ts_enum.is_const:
            signature_parts.append("const")

        signature_parts.append("enum")
        signature_parts.append(ts_enum.name)

        return " ".join(signature_parts)

    def _add_enum_members_section(
        self, ts_enum: TSEnum, content_nodes: list[nodes.Node]
    ) -> None:
        """Add enum members section."""
        if not ts_enum.members:
            return

        # Add a section header for members
        members_section = nodes.section()
        members_section["ids"] = [f"enum-{ts_enum.name}-members"]

        # Create members title
        title = nodes.title()
        title += nodes.Text("Members")
        members_section += title

        # Add each member as individual documentation
        for member in ts_enum.members:
            member_nodes = self._format_enum_member(member, ts_enum.name)
            for member_node in member_nodes:
                members_section += member_node

        content_nodes.append(members_section)

    def _format_enum_member(
        self, member: TSEnumMember, enum_name: str
    ) -> list[nodes.Node]:
        """Format an enum member."""
        member_nodes = []

        # Create standardized enum member descriptor
        desc_node, sig_node, desc_content = self._create_standard_desc_node(
            "enum_member", member.name, parent_name=enum_name
        )

        # Create member signature with qualified name
        sig_node += addnodes.desc_addname(f"{enum_name}.", f"{enum_name}.")
        member_name_node = addnodes.desc_sig_name(member.name, member.name)
        member_name_node["classes"] = ["sig-name", "descname"]
        sig_node += member_name_node

        # Add value if present
        if member.value is not None:
            sig_node += addnodes.desc_annotation(
                f" = {member.value}", f" = {member.value}"
            )

        # Add standardized documentation content, but skip complex directives
        # that might cause issues in enum member contexts
        if member.doc_comment and member.doc_comment.description:
            self._add_standard_doc_content(
                desc_content, member.doc_comment, skip_examples=True
            )
        else:
            # Add a simple note if no documentation is available
            para = nodes.paragraph()
            para += nodes.emphasis(text="No description available.")
            desc_content += para

        member_nodes.append(desc_node)

        return member_nodes

    def _create_member_signature(self, member: TSEnumMember) -> str:
        """Create the member signature string."""
        signature = member.name

        if member.value is not None:
            signature += f" = {member.value}"

        return signature
