"""Base TypeScript Auto-Directive Module.

Contains the base TSAutoDirective class that provides common functionality
for all TypeScript auto-documentation directives.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import directives
from docutils.utils import SystemMessage
from sphinx import addnodes
from sphinx.util import logging as sphinx_logging
from sphinx.util.docutils import SphinxDirective

from sphinx_ts.parser import TSDocComment, TSMethod, TSParser, TSProperty

logger = sphinx_logging.getLogger(__name__)


class TSAutoDirective(SphinxDirective):
    """Base class for TypeScript auto-directives."""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "members": directives.unchanged,
        "undoc-members": directives.flag,
        "show-inheritance": directives.flag,
        "member-order": directives.unchanged,
        "exclude-members": directives.unchanged,
        "private-members": directives.flag,
        "special-members": directives.unchanged,
        "imported-members": directives.flag,
        "ignore-module-all": directives.flag,
        "no-index": directives.flag,
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the directive."""
        super().__init__(*args, **kwargs)
        self.parser = TSParser()
        self.logger = logging.getLogger(__name__)

    def get_source_files(self) -> list[Path]:
        """Get list of TypeScript source files to scan."""
        src_dirs = self.config.sphinx_ts_src_dirs or ["."]
        exclude_patterns = self.config.sphinx_ts_exclude_patterns or []

        source_files = []

        for src_dir in src_dirs:
            src_path = Path(self.env.srcdir) / src_dir
            if src_path.exists():
                for ts_file in src_path.rglob("*.ts"):
                    # Check if file should be excluded
                    relative_path = ts_file.relative_to(Path(self.env.srcdir))
                    if not any(
                        relative_path.match(pattern)
                        for pattern in exclude_patterns
                    ):
                        source_files.append(ts_file)

        return source_files

    def find_object_in_files(
        self,
        object_name: str,
        object_type: str,
    ) -> dict[str, Any] | None:
        """Find a specific object in TypeScript files."""
        source_files = self.get_source_files()

        for file_path in source_files:
            try:
                parsed_data = self.parser.parse_file(file_path)

                # Map object types to their plural forms in parsed data
                type_mapping = {
                    "class": "classes",
                    "interface": "interfaces",
                    "variable": "variables",
                    "function": "functions",
                    "enum": "enums",
                    "type": "types",
                }
                plural_type = type_mapping.get(object_type, object_type + "s")
                objects = parsed_data.get(plural_type, [])

                for obj in objects:
                    # Handle both object-style and dict-style objects
                    if isinstance(obj, dict):
                        obj_name = obj.get("name")
                    else:
                        obj_name = getattr(obj, "name", None)
                    if obj_name:
                        if obj_name == object_name:
                            obj_data = {
                                "object": obj,
                                "file_path": file_path,
                                "parsed_data": parsed_data,
                            }
                            # Register this object with the domain for cross-ref
                            self._register_object_with_domain(
                                object_type, obj_name, self.env.docname
                            )
                            return obj_data
                        if obj_name.lower() == object_name.lower():
                            # Try case-insensitive match if exact match fails
                            obj_data = {
                                "object": obj,
                                "file_path": file_path,
                                "parsed_data": parsed_data,
                            }
                            # Register this object with the domain for cross-ref
                            self._register_object_with_domain(
                                object_type, obj_name, self.env.docname
                            )
                            return obj_data

            except Exception as e:
                logger.warning("Failed to parse %s: %s", file_path, e)
                continue

        return None

    def _register_object_with_domain(
        self,
        obj_type: str,
        name: str,
        docname: str,
        *,
        noindex: bool = False,
    ) -> None:
        """Register an object with the TypeScript domain for cross-referencing.

        Args:
            obj_type: The type of object (class, method, property, etc.)
            name: The name of the object
            docname: The document name
            noindex: If True, the object won't appear in the index/TOC

        """
        # Get the TypeScript domain
        # Register the object with the TypeScript domain for cross-referencing
        ts_domain = self.env.get_domain("ts")

        # Register the object with the domain - ensure obj_type is a string
        obj_type_str = str(obj_type)
        ts_domain.data["objects"].setdefault(obj_type_str, {})

        # Store as a tuple with docname, display name, and noindex flag
        ts_domain.data["objects"][obj_type_str][name] = (docname, name, noindex)

    def format_doc_comment(
        self,
        doc_comment: TSDocComment | None,
        *,
        skip_params: bool = False,
        skip_returns: bool = False,
        skip_examples: bool = False,
    ) -> list[str]:
        """Format a JSDoc comment as reStructuredText."""
        if not doc_comment:
            return []

        lines = []

        # Add description with better paragraph handling
        if doc_comment.description:
            # Split into paragraphs and format each one
            paragraphs = doc_comment.description.strip().split("\n\n")
            for i, paragraph in enumerate(paragraphs):
                # Clean up each paragraph
                clean_paragraph = " ".join(
                    line.strip()
                    for line in paragraph.split("\n")
                    if line.strip()
                )
                if clean_paragraph:
                    lines.append(clean_paragraph)
                    if (
                        i < len(paragraphs) - 1
                    ):  # Add spacing between paragraphs
                        lines.append("")
            lines.append("")

        # Add deprecation notice with better formatting
        if doc_comment.deprecated:
            deprecated_text = (
                doc_comment.deprecated or "This feature is deprecated."
            )

            # Check if deprecated text starts with a version number
            version_pattern = r"^\s*v?\d+\.\d+"
            if re.match(version_pattern, deprecated_text):
                # Text starts with version, use standard deprecated directive
                lines.extend([f".. deprecated:: {deprecated_text}", ""])
            else:
                # No version number, use warning directive to avoid parsing
                lines.extend(
                    [
                        ".. warning::",
                        f"   **Deprecated:** {deprecated_text}",
                        "",
                    ]
                )

        # Add since version with cleaner formatting
        if doc_comment.since:
            lines.extend([".. versionadded::", f"   {doc_comment.since}", ""])

        # Add parameters only if not skipped
        if not skip_params:
            lines.extend(self._format_parameters(doc_comment))

        # Add return information if not skipped
        if not skip_returns:
            lines.extend(self._format_returns(doc_comment))

        # Add examples only if not skipped
        if not skip_examples:
            lines.extend(self._format_examples(doc_comment))

        # Add other tags
        lines.extend(self._format_other_tags(doc_comment))

        return lines

    def _format_parameters(self, doc_comment: TSDocComment) -> list[str]:
        """Format parameter documentation with proper RST definition lists."""
        if not doc_comment.params:
            return []

        lines = ["**Parameters:**", ""]

        for param_name, param_desc in doc_comment.params.items():
            # Create proper RST definition list format
            lines.append(f"``{param_name}``")
            if param_desc:
                # Proper indentation for definition list items
                desc_lines = param_desc.strip().split("\n")
                for i, line in enumerate(desc_lines):
                    if i == 0:
                        lines.append(f"    {line.strip()}")
                    else:
                        lines.append(f"    {line.strip()}")
            else:
                lines.append("    ")
            lines.append("")

        return lines

    def _format_returns(self, doc_comment: TSDocComment) -> list[str]:
        """Format return value documentation as RST lines.

        This is used for RST generation in format_doc_comment.
        For node-based documentation, use format_returns_section instead.

        The format_returns_section method is the preferred way to handle
        returns since it can combine both JSDoc @returns description and
        TypeScript return type information.
        """
        if not doc_comment.returns:
            return []

        return ["**Returns:**", "", doc_comment.returns.strip(), ""]

    def format_returns_section(
        self,
        content: nodes.Element,
        doc_comment: TSDocComment | None,
        return_type: str | None = None,
    ) -> None:
        """Add returns section to documentation.

        This is a shared method for displaying return information consistently
        across different TypeScript objects (functions, methods, variables).
        It handles both
        the JSDoc @returns tag description and the TypeScript return type.

        Args:
            content: The content container to add the returns section to
            doc_comment: Optional doc comment containing returns information
            return_type: Optional return type if not available in doc_comment

        Note:
            When both doc_comment.returns and return_type are provided, the
            doc_comment.returns takes precedence as it typically contains more
            descriptive information.

        """
        # Only add returns section if we have content
        if not ((doc_comment and doc_comment.returns) or return_type):
            return

        returns_rubric = nodes.rubric(text="Returns")

        content.append(returns_rubric)

        # Create paragraph for the return content
        returns_para = nodes.paragraph()

        # Add return type if available
        if return_type:
            formatted_type = self.format_parameter_type(return_type)
            if formatted_type:
                returns_para.append(nodes.emphasis("", formatted_type))

                # Add separator if we also have a description
                if doc_comment and doc_comment.returns:
                    returns_para.append(nodes.Text(" - "))

        # Add return description if available
        if doc_comment and doc_comment.returns:
            returns_para.append(nodes.Text(doc_comment.returns))

        content.append(returns_para)

    def _format_examples(self, doc_comment: TSDocComment) -> list[str]:
        """Format example documentation with better styling."""
        lines = []
        if doc_comment.examples:
            lines.extend(["**Examples:**", ""])

            for i, example in enumerate(doc_comment.examples):
                # Add separator between multiple examples
                if i > 0:
                    lines.append("")

                # Format code block with proper indentation
                lines.extend([".. code-block:: typescript", ""])

                # Clean up and indent the example code
                example_lines = example.strip().split("\n")
                for line in example_lines:
                    lines.append(f"   {line}")
                lines.append("")

            lines.append("")
            # Remove final empty line to avoid double spacing
            if lines and lines[-1] == "":
                lines.pop()
        return lines

    def _format_other_tags(self, doc_comment: TSDocComment) -> list[str]:
        """Format other documentation tags."""
        lines = []

        # Handle custom tags with better formatting
        if doc_comment.tags:
            for tag_name, tag_value in doc_comment.tags.items():
                # Clean up tag value
                clean_value = tag_value.strip() if tag_value else ""
                if not clean_value:
                    continue

                if tag_name.lower() in ["see", "seealso"]:
                    lines.extend([".. seealso::", f"   {clean_value}", ""])
                elif tag_name.lower() in ["note", "notes"]:
                    lines.extend([".. note::", f"   {clean_value}", ""])
                elif tag_name.lower() in ["warning", "warn"]:
                    lines.extend([".. warning::", f"   {clean_value}", ""])
                elif tag_name.lower() == "todo":
                    lines.extend([".. todo::", f"   {clean_value}", ""])
                elif tag_name.lower() in ["throws", "throw"]:
                    lines.extend(["**Raises:**", f"{clean_value}", ""])
                else:
                    # For unknown tags, use a generic format
                    lines.extend(
                        [f"**{tag_name.title()}:**", f"{clean_value}", ""]
                    )

        return lines

    def format_type_annotation(self, type_annotation: str | None) -> str:
        """Format TypeScript type annotation."""
        if not type_annotation:
            return "any"

        # Clean up the type annotation
        cleaned = type_annotation.strip()
        cleaned = cleaned.removeprefix(":").strip()

        # Format union types to have consistent spacing
        if "|" in cleaned:
            # Split on union operators and clean each part
            union_parts = []
            parts = cleaned.split("|")
            for part in parts:
                # Clean up excessive whitespace and newlines
                clean_part = " ".join(part.split())
                # Only add non-empty parts (handles leading | characters)
                if clean_part:
                    union_parts.append(clean_part)
            # Join with consistent spacing
            cleaned = " | ".join(union_parts)
        else:
            # For non-union types, just normalize whitespace
            cleaned = " ".join(cleaned.split())

        return cleaned

    def format_optional_parameter(
        self,
        node: nodes.Element,
        param_name: str,
        optional: bool,
        *,
        in_signature: bool = False,
    ) -> nodes.Element:
        """Format optional parameter consistently.

        Args:
            node: Node to append the parameter to
            param_name: The name of the parameter
            optional: Whether the parameter is optional
            in_signature: Whether this is in a signature (use ? instead of text)

        Returns:
            The node with parameter formatting applied

        """
        # Add parameter name
        name_node = addnodes.desc_name("", param_name)
        node += name_node

        # Add optional marker according to context
        if optional:
            if in_signature:
                # In signature, we handle optional markers differently
                # This is handled separately in signature generation
                pass
            else:
                # In documentation, use (optional)
                node += nodes.emphasis("", " (optional)")

        return node

    def format_parameter_type(
        self,
        param_type: str | None,
        *,
        add_colon: bool = False,
    ) -> str:
        """Format a parameter type consistently.

        Args:
            param_type: The parameter type to format
            add_colon: Whether to prepend a colon to the type

        Returns:
            Formatted parameter type

        """
        if not param_type:
            return ""

        # Use the existing format_type_annotation method for consistency
        formatted = self.format_type_annotation(param_type)
        return f": {formatted}" if add_colon else formatted

    def format_parameter_nodes(
        self, parameter: nodes.Element, param: dict
    ) -> None:
        """Format a parameter node for signatures.

        Args:
            parameter: The node to add parameter formatting to
            param: Parameter dictionary with name, type, optional, and default

        """
        param_name = param.get("name", "")
        param_type = param.get("type", "")
        optional = param.get("optional", False)
        default_val = param.get("default")

        # Add parameter name
        parameter += addnodes.desc_sig_name(param_name, param_name)

        # Add type annotation
        if param_type:
            parameter += nodes.Text(": ")
            formatted_type = self.format_parameter_type(param_type)
            parameter += nodes.emphasis("", formatted_type)

        # Add optional marker (?) for optional parameters with no default
        if optional and not default_val:
            parameter += nodes.Text("?")

        # Add default value if present
        if default_val:
            parameter += nodes.Text(f" = {default_val}")

    def format_parameter_string(self, param: dict) -> str:
        """Format a parameter as a string for signatures.

        Args:
            param: Parameter dictionary with name, type, optional, and default

        Returns:
            Formatted parameter string for signatures

        """
        param_str = param["name"]

        # Add type if present
        if param.get("type"):
            type_str = self.format_parameter_type(param.get("type"))
            param_str += f": {type_str}"

        # Add ? for optional parameters (only if no default value)
        if param.get("optional") and not param.get("default"):
            param_str += "?"

        # Add default value if present
        if param.get("default"):
            param_str += f" = {param.get('default')}"

        return param_str

    def create_rst_content(self, lines: list[str]) -> list[nodes.Node]:
        """Convert RST content lines to docutils nodes."""
        if not lines:
            return []

        # Join lines and parse as RST
        content = "\n".join(lines)

        try:
            doctree = publish_doctree(content)
            return list(doctree.children)
        except SystemMessage:
            # Fallback to simple paragraph
            return [nodes.paragraph(text=content)]

    def _process_object_common(
        self,
        object_name: str,
        object_type: str,
        not_found_message: str | None = None,
        log_level: int = logging.WARNING,
    ) -> dict[str, Any] | None:
        """Find and register objects using a common pattern.

        Args:
            object_name: Name of the object to find
            object_type: Type of object (class, interface, enum, etc.)
            not_found_message: Custom warning message if object not found
            log_level: Logging level for not found message (default: WARNING)

        Returns:
            Dict with object data or None if not found

        """
        # Find the object in source files
        result = self.find_object_in_files(object_name, object_type)
        if not result:
            message = (
                not_found_message
                or f"Could not find TypeScript {object_type}: {object_name}"
            )
            logger.log(log_level, message)
            return None

        # Register the object with the TypeScript domain
        self._register_object_with_domain(
            object_type, object_name, self.env.docname
        )

        return result

    def _format_method_common(
        self,
        method: TSMethod,
        parent_name: str | None = None,
        title_override: str | None = None,
    ) -> addnodes.desc | None:
        """Format a method as RST.

        This shared method can be used by both class and interface directives.

        Args:
            method: The method to format
            parent_name: Optional parent class/interface name
            title_override: Optional title override

        Returns:
            A formatted method description (not a section to avoid TOC entries)

        """
        if not method.name:
            return None

        method_id = (
            f"{parent_name}.{method.name}" if parent_name else method.name
        )

        # Create method description directly (no section wrapper)
        desc = addnodes.desc(
            domain="ts",
            objtype="method",
            noindex=True,  # Don't index this in the global index
        )
        desc["ids"] = [f"ts-method-{method_id}"]

        # Create signature for method
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = "sig-object ts ts-method"
        sig["ids"] = [f"method-{method_id}"]
        desc += sig

        # Add method name with explicit CSS class for red styling
        name = title_override or method.name
        method_name_node = addnodes.desc_sig_name(name, name)
        method_name_node["classes"] = ["sig-name", "descname"]
        sig += method_name_node

        # Add method parameters
        paramlist = addnodes.desc_parameterlist()
        sig += paramlist

        # Add each parameter in a more compact format
        if method.parameters:
            for param in method.parameters:
                parameter = addnodes.desc_parameter("", "")
                paramlist += parameter

                # Use the shared parameter formatting helper
                self.format_parameter_nodes(parameter, param)

        # Add return type on the same line as the method signature
        if method.return_type:
            sig += nodes.Text(": ")
            formatted_type = self.format_parameter_type(method.return_type)
            sig += nodes.emphasis("", formatted_type)

        # Add content container
        content = addnodes.desc_content()
        desc += content

        # Add method documentation first (description only)
        self._add_method_description(content, method)

        # Then add parameter information
        self._add_parameter_list(content, method)

        # Then add returns information
        self._add_method_returns(content, method)

        # Add examples documentation
        if method.doc_comment:
            self._add_examples_section(content, method.doc_comment)

        return desc

    def _add_method_description(
        self, content: addnodes.desc_content, method: TSMethod
    ) -> None:
        """Add method description with better paragraph handling."""
        if method.doc_comment and method.doc_comment.description:
            # Split description into paragraphs for better formatting
            paragraphs = method.doc_comment.description.strip().split("\n\n")
            for paragraph in paragraphs:
                # Clean up paragraph text
                clean_text = " ".join(
                    line.strip()
                    for line in paragraph.split("\n")
                    if line.strip()
                )
                if clean_text:
                    desc_para = nodes.paragraph()
                    desc_para.append(nodes.Text(clean_text))
                    content.append(desc_para)

    def _add_method_returns(
        self, content: addnodes.desc_content, method: TSMethod
    ) -> None:
        """Add method returns information."""
        if method.return_type or (
            method.doc_comment and method.doc_comment.returns
        ):
            # Add returns directly to the content
            self.format_returns_section(
                content, method.doc_comment, method.return_type
            )

    def _add_parameter_list(
        self, content: addnodes.desc_content, method: TSMethod
    ) -> None:
        """Add parameter list with improved styling and layout."""
        if not method.parameters:
            return

        # Extract documented parameters from doc_comment if it exists
        documented_params = {}
        if method.doc_comment and method.doc_comment.params:
            documented_params = method.doc_comment.params

        # Add parameters section with better styling
        param_section = nodes.section()
        param_section["ids"] = ["parameters"]

        param_title = nodes.title(text="Parameters")
        param_section.append(param_title)

        # Use definition list for cleaner parameter display
        definition_list = nodes.definition_list()
        param_section.append(definition_list)

        # Add parameters as definition list items
        for param in method.parameters:
            # Create definition list item
            def_item = nodes.definition_list_item()
            definition_list.append(def_item)

            # Create term (parameter name with type)
            term = nodes.term()
            def_item.append(term)

            # Add parameter name with optional marker
            param_name = nodes.literal(text=param["name"])
            term.append(param_name)

            if param.get("optional", False):
                term.append(nodes.Text("?"))

            # Add type information
            if param.get("type"):
                term.append(nodes.Text(": "))
                formatted_type = self.format_parameter_type(
                    param.get("type", "")
                )
                type_node = nodes.emphasis(text=formatted_type)
                term.append(type_node)

            # Add default value if present
            if param.get("default"):
                term.append(nodes.Text(f" = {param.get('default')}"))

            # Create definition (parameter description)
            definition = nodes.definition()
            def_item.append(definition)

            if param["name"] in documented_params:
                desc_para = nodes.paragraph()
                desc_para.append(nodes.Text(documented_params[param["name"]]))
                definition.append(desc_para)
            else:
                # Add empty paragraph to maintain structure
                empty_para = nodes.paragraph()
                definition.append(empty_para)

        content.append(param_section)

    def _format_property_common(
        self, prop: TSProperty, parent_name: str | None = None
    ) -> addnodes.desc | None:
        """Format a property as RST with improved styling.

        This shared method can be used by both class and interface directives.

        Args:
            prop: The property to format
            parent_name: Optional parent class/interface name

        Returns:
            A formatted property description (not a section for TOC)

        """
        prop_id = f"{parent_name}.{prop.name}" if parent_name else prop.name

        # Create property description directly (no section wrapper)
        desc = addnodes.desc(
            domain="ts",
            objtype="attribute",
        )
        desc["ids"] = [f"ts-property-{prop_id}"]

        # Create signature with better styling
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = "sig-object ts ts-property"
        sig["ids"] = [f"property-{prop_id}"]
        desc += sig

        # Add property name with explicit CSS class for red styling
        prop_name_node = addnodes.desc_sig_name(prop.name, prop.name)
        prop_name_node["classes"] = ["sig-name", "descname"]
        sig += prop_name_node

        # Add optional marker for properties if needed
        if hasattr(prop, "is_optional") and prop.is_optional:
            optional_node = nodes.inline("?", "?")
            optional_node["classes"] = ["optional-marker"]
            sig += optional_node

        # Add property type with better formatting
        if prop.type_annotation:
            sig += nodes.Text(": ")
            formatted_type = self.format_parameter_type(prop.type_annotation)
            type_node = nodes.emphasis("", formatted_type)
            type_node["classes"] = ["type-annotation"]
            sig += type_node

        # Add default value if present
        if hasattr(prop, "default_value") and prop.default_value:
            sig += nodes.Text(f" = {prop.default_value}")

        # Add content container
        content = addnodes.desc_content()
        desc += content

        # Add property documentation with better paragraph handling
        if prop.doc_comment and prop.doc_comment.description:
            # Split description into paragraphs for better formatting
            paragraphs = prop.doc_comment.description.strip().split("\n\n")
            for paragraph in paragraphs:
                clean_text = " ".join(
                    line.strip()
                    for line in paragraph.split("\n")
                    if line.strip()
                )
                if clean_text:
                    para = nodes.paragraph()
                    para += nodes.Text(clean_text)
                    content += para

        return desc

    def _add_examples_section(
        self,
        content: nodes.Element,
        doc_comment: TSDocComment,
    ) -> None:
        """Add examples section to documentation content with improved styling.

        Args:
            content: The content container to add examples to
            doc_comment: The doc comment containing examples

        """
        if not (doc_comment and doc_comment.examples):
            return

        # Create examples section with consistent styling
        examples_section = nodes.section()
        examples_section["ids"] = ["examples"]

        examples_title = nodes.title(text="Examples")
        examples_section.append(examples_title)

        # Process each example individually for better separation
        for i, example in enumerate(doc_comment.examples):
            # Add spacing between multiple examples
            if i > 0:
                separator = nodes.paragraph()
                examples_section.append(separator)

            # Clean up example text
            example_text = example.strip()

            # Create code block with proper formatting
            example_node = nodes.literal_block(example_text, example_text)
            example_node["language"] = "typescript"
            example_node["classes"] = ["highlight", "ts-example"]
            examples_section.append(example_node)

        content.append(examples_section)

    def _register_members_with_domain(
        self,
        parent_name: str,
        methods: list | None = None,
        properties: list | None = None,
        *,
        noindex: bool = True,
    ) -> None:
        """Register methods and properties with the domain.

        Args:
            parent_name: Name of the parent class/interface
            methods: List of methods to register
            properties: List of properties to register
            noindex: Whether to exclude from TOC (default True for members)

        """
        # Register only methods with domain
        if methods:
            for method in methods:
                if hasattr(method, "name") and method.name:
                    qualified_name = f"{parent_name}.{method.name}"
                    self._register_object_with_domain(
                        "method",
                        qualified_name,
                        self.env.docname,
                        noindex=noindex,
                    )

        if properties:
            for prop in properties:
                if hasattr(prop, "name") and prop.name:
                    qualified_name = f"{parent_name}.{prop.name}"
                    self._register_object_with_domain(
                        "property",
                        qualified_name,
                        self.env.docname,
                        noindex=noindex,
                    )

    def _create_standard_desc_node(
        self,
        objtype: str,
        name: str,
        parent_name: str | None = None,
    ) -> tuple[addnodes.desc, addnodes.desc_signature, addnodes.desc_content]:
        """Create a standardized desc node structure.

        This provides consistent formatting across all directive types.

        Args:
            objtype: The object type (class, interface, enum, etc.)
            name: The name of the object
            parent_name: Optional parent name for qualified names

        Returns:
            Tuple of (desc_node, signature_node, content_node) for further
            customization

        """
        qualified_name = f"{parent_name}.{name}" if parent_name else name

        # Create the main desc node
        desc = addnodes.desc(domain="ts", objtype=objtype)
        desc["ids"] = [f"{objtype}-{qualified_name}"]

        # Create signature
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = f"sig-object ts ts-{objtype}"
        sig["ids"] = [f"{objtype}-{qualified_name}"]
        sig["fullname"] = qualified_name
        desc += sig

        # Create content container
        content = addnodes.desc_content()
        desc += content

        return desc, sig, content

    def _add_standard_doc_content(
        self,
        content_node: addnodes.desc_content,
        doc_comment: TSDocComment | None,
        *,
        skip_params: bool = False,
        skip_returns: bool = False,
        skip_examples: bool = False,
    ) -> None:
        """Add standardized documentation content to a content node.

        Args:
            content_node: The content node to add documentation to
            doc_comment: The doc comment to format
            skip_params: Whether to skip parameter documentation
            skip_returns: Whether to skip return documentation
            skip_examples: Whether to skip example documentation

        """
        if not doc_comment:
            return

        try:
            # Format the doc comment as RST and parse it into proper nodes
            formatted_rst_lines = self.format_doc_comment(
                doc_comment,
                skip_params=skip_params,
                skip_returns=skip_returns,
                skip_examples=skip_examples,
            )

            if formatted_rst_lines:
                from docutils.statemachine import StringList  # noqa: PLC0415

                # Use Sphinx's content parsing mechanism
                content = StringList(formatted_rst_lines)
                node = nodes.Element()
                self.state.nested_parse(content, self.content_offset, node)

                # Add the parsed content
                for child in node.children:
                    content_node.append(child)

        except Exception as e:
            # Fallback to plain text if RST parsing fails
            logger.warning(
                "Failed to parse RST content: %s",
                e,
            )
            if doc_comment and doc_comment.description:
                desc_para = nodes.paragraph()
                desc_para.append(nodes.Text(doc_comment.description))
                content_node.append(desc_para)

    def _create_standard_signature(
        self,
        sig_node: addnodes.desc_signature,
        name: str,
        annotation: str = "",
        type_params: list[str] | None = None,
        extends: list[str] | None = None,
        modifiers: list[str] | None = None,
    ) -> None:
        """Create a standardized signature with consistent formatting.

        Args:
            sig_node: The signature node to populate
            name: The main name of the object
            annotation: Optional annotation (e.g., "class", "interface")
            type_params: Optional type parameters
            extends: Optional extends clauses
            modifiers: Optional modifiers (export, declare, etc.)

        """
        # Add modifiers first
        if modifiers:
            for modifier in modifiers:
                sig_node += addnodes.desc_annotation(
                    f"{modifier} ", f"{modifier} "
                )

        # Add annotation (class, interface, etc.)
        if annotation:
            sig_node += addnodes.desc_annotation(
                f"{annotation} ", f"{annotation} "
            )

        # Add main name (use desc_name for main object declarations)
        sig_node += addnodes.desc_name("", name)

        # Add type parameters
        if type_params:
            sig_node += nodes.Text(f"<{', '.join(type_params)}>")

        # Add extends clause
        if extends:
            sig_node += nodes.Text(f" extends {', '.join(extends)}")
