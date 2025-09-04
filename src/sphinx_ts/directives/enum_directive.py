"""TypeScript Enum Auto-Directive Module.

Contains the TSAutoEnumDirective class for auto-documenting TypeScript enums.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from docutils import nodes
from docutils.utils import SystemMessage
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
        # Create the main description node
        desc_node = addnodes.desc(
            domain="ts",
            objtype="enum",
            noindex=False,
        )
        desc_node["ids"] = [f"enum-{ts_enum.name}"]

        # Create signature node
        sig_node = addnodes.desc_signature("", "", first=True)
        sig_node["class"] = "sig-object ts"
        sig_node["ids"] = [f"enum-{ts_enum.name}"]
        sig_node["fullname"] = ts_enum.name

        # Add enum modifiers and keyword
        signature_parts = []
        if ts_enum.is_export:
            signature_parts.append("export")
            sig_node += addnodes.desc_annotation("export ", "export ")

        if ts_enum.is_declare:
            signature_parts.append("declare")
            sig_node += addnodes.desc_annotation("declare ", "declare ")

        if ts_enum.is_const:
            signature_parts.append("const")
            sig_node += addnodes.desc_annotation("const ", "const ")

        sig_node += addnodes.desc_annotation("enum ", "enum ")
        sig_node += addnodes.desc_name(ts_enum.name, ts_enum.name)

        desc_node += sig_node

        # Add description content
        desc_content = addnodes.desc_content()

        # Add enum description
        if ts_enum.doc_comment and ts_enum.doc_comment.description:
            para = nodes.paragraph()
            para += nodes.Text(ts_enum.doc_comment.description)
            desc_content += para

        # Add members in a codeblock
        if ts_enum.members:
            members_para = nodes.paragraph()
            members_para += nodes.strong(text="Members:")
            desc_content += members_para

            # Create a codeblock with the members
            member_lines = []
            for i, member in enumerate(ts_enum.members):
                # Add JSDoc comment if present
                if member.doc_comment and member.doc_comment.description:
                    comment_text = member.doc_comment.description.strip()
                    member_lines.append(f"/** {comment_text} */")

                # Add member signature with comma
                member_sig = self._create_member_signature(member)
                # Add comma except for the last member
                if i < len(ts_enum.members) - 1:
                    member_sig += ","
                member_lines.append(member_sig)

            codeblock = nodes.literal_block()
            codeblock["language"] = "typescript"
            codeblock += nodes.Text("\n".join(member_lines))
            desc_content += codeblock

        desc_node += desc_content
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
        # Members are now added inline in the main description

    def _format_enum_member(self, member: TSEnumMember) -> list[nodes.Node]:
        """Format an enum member."""
        member_nodes = []

        # Create member signature
        member_signature = self._create_member_signature(member)

        # Create signature node
        sig_node = addnodes.desc_signature()
        sig_node["fullname"] = member.name
        sig_node += addnodes.desc_name(text=member_signature)

        # Create the main description node
        desc_node = addnodes.desc()
        desc_node["objtype"] = "enum_member"
        desc_node["noindex"] = True
        desc_node += sig_node

        # Add description content
        desc_content = addnodes.desc_content()
        if member.doc_comment:
            desc_text = self.format_doc_comment(member.doc_comment)
            if desc_text:
                # Filter out complex directives for member comments too
                filtered_text = []
                filtered_text = [
                    line
                    for line in desc_text
                    if not line.strip().startswith(".. ")
                ]

                if filtered_text:
                    try:
                        rst_content = self.create_rst_content(filtered_text)
                        desc_content.extend(rst_content)
                    except (SystemMessage, ValueError) as e:
                        logger.warning("Failed to parse RST content: %s", e)
                        # Fallback to simple text
                        para = nodes.paragraph()
                        para += nodes.Text(member.doc_comment.description)
                        desc_content += para

        desc_node += desc_content
        member_nodes.append(desc_node)

        return member_nodes

    def _create_member_signature(self, member: TSEnumMember) -> str:
        """Create the member signature string."""
        signature = member.name

        if member.value is not None:
            signature += f" = {member.value}"

        return signature
