"""Base TypeScript Auto-Directive Module.

Contains the base TSAutoDirective class that provides common functionality
for all TypeScript auto-documentation directives.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import directives
from docutils.utils import SystemMessage
from sphinx import addnodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from sphinx_ts.parser import TSDocComment, TSParser

logger = logging.getLogger(__name__)


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

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize the directive."""
        super().__init__(*args, **kwargs)
        self.parser = TSParser()

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
                }
                plural_type = type_mapping.get(object_type, object_type + "s")
                objects = parsed_data.get(plural_type, [])

                for obj in objects:
                    if hasattr(obj, "name"):
                        if obj.name == object_name:
                            obj_data = {
                                "object": obj,
                                "file_path": file_path,
                                "parsed_data": parsed_data,
                            }
                            # Register this object with the domain for cross-ref
                            self._register_object_with_domain(
                                object_type, obj.name, self.env.docname
                            )
                            return obj_data
                        if obj.name.lower() == object_name.lower():
                            # Try case-insensitive match if exact match fails
                            obj_data = {
                                "object": obj,
                                "file_path": file_path,
                                "parsed_data": parsed_data,
                            }
                            # Register this object with the domain for cross-ref
                            self._register_object_with_domain(
                                object_type, obj.name, self.env.docname
                            )
                            return obj_data

            except Exception as e:  # noqa: BLE001
                logger.warning("Failed to parse %s: %s", file_path, e)
                continue

        return None

    def _register_object_with_domain(
        self, obj_type: str, name: str, docname: str, noindex: bool = False
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
        skip_params: bool = False,
        skip_returns: bool = False,
        skip_examples: bool = False,
    ) -> list[str]:
        """Format a JSDoc comment as reStructuredText."""
        if not doc_comment:
            return []

        lines = []

        # Add description
        if doc_comment.description:
            lines.extend(doc_comment.description.split("\n"))
            lines.append("")

        # Add deprecation notice if present
        if doc_comment.deprecated:
            lines.extend(
                [
                    ".. warning::",
                    "",
                    "   **Deprecated**: "
                    + (doc_comment.deprecated or "This feature is deprecated."),
                    "",
                ]
            )

        # Add since version if available
        if doc_comment.since:
            lines.extend(
                [
                    ".. note::",
                    "",
                    f"   Available since version {doc_comment.since}",
                    "",
                ]
            )

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
        """Format parameter documentation."""
        if not doc_comment.params:
            return []

        lines = [".. rubric:: Parameters", ""]
        lines.append(".. list-table::")
        lines.append("   :widths: 20 80")
        lines.append("   :class: parameter-table")
        lines.append("")

        for param_name, param_desc in doc_comment.params.items():
            param_node_txt = f":{param_name}:"
            lines.append(f"   * - ``{param_node_txt}``")
            if param_desc:
                lines.append(f"     - {param_desc}")
            else:
                lines.append("     - ")

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

        lines = [".. rubric:: Returns", ""]
        lines.append("   " + doc_comment.returns)
        lines.append("")
        return lines

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
        """Format example documentation."""
        lines = []
        if doc_comment.examples:
            lines.append(".. rubric:: Examples")
            lines.append("")
            # Use only one code block for all examples to prevent duplication
            lines.append(".. code-block:: typescript")
            lines.append("")
            for example in doc_comment.examples:
                lines.extend(f"   {line}" for line in example.split("\n"))
                if example != doc_comment.examples[-1]:
                    lines.append("   ")  # Add separator between examples
            lines.append("")
        return lines

    def _format_other_tags(self, doc_comment: TSDocComment) -> list[str]:
        """Format other documentation tags."""
        lines = []
        if doc_comment.since:
            lines.extend([f":Since: {doc_comment.since}", ""])
        if doc_comment.deprecated:
            lines.extend([f".. deprecated:: {doc_comment.deprecated}", ""])
        return lines

    def format_type_annotation(self, type_annotation: str | None) -> str:
        """Format TypeScript type annotation."""
        if not type_annotation:
            return "any"

        # Clean up the type annotation
        cleaned = type_annotation.strip()
        return cleaned.removeprefix(":").strip()

    def format_optional_parameter(
        self,
        node: nodes.Element,
        param_name: str,
        optional: bool,
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
        self, param_type: str | None, add_colon: bool = False
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
        parameter += addnodes.desc_sig_name("", param_name)

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
    ) -> dict[str, Any] | None:
        """Find and register objects using a common pattern.

        Args:
            object_name: Name of the object to find
            object_type: Type of object (class, interface, enum, etc.)
            not_found_message: Custom warning message if object not found

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
            logger.warning(message)
            return None

        # Register the object with the TypeScript domain
        self._register_object_with_domain(
            object_type, object_name, self.env.docname
        )

        return result

    def _format_method_common(
        self,
        method: Any,
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
        sig["class"] = "sig-object ts"
        sig["ids"] = [f"method-{method_id}"]
        desc += sig

        # Add method name
        name = title_override or method.name
        sig += addnodes.desc_name("", name)

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
        self._add_examples_section(content, method.doc_comment)

        return desc

    def _add_method_description(
        self, content: addnodes.desc_content, method: Any
    ) -> None:
        """Add method description only (no parameters, returns, or examples)."""
        if method.doc_comment and method.doc_comment.description:
            desc_para = nodes.paragraph()
            desc_para.append(nodes.Text(method.doc_comment.description))
            content.append(desc_para)

    def _add_method_returns(
        self, content: addnodes.desc_content, method: Any
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
        self, content: addnodes.desc_content, method: Any
    ) -> None:
        """Add parameter list to method content."""
        if not method.parameters:
            return

        # Extract documented parameters from doc_comment if it exists
        documented_params = {}
        if method.doc_comment and method.doc_comment.params:
            documented_params = method.doc_comment.params

        # Add a rubric for parameters (without colon, Sphinx adds formatting)
        param_rubric = nodes.rubric(text="Parameters")
        content.append(param_rubric)

        # Create field list for parameters
        field_list = nodes.field_list()
        content.append(field_list)

        # Add parameters as field items
        for param in method.parameters:
            # Create field item
            field = nodes.field()
            field_list.append(field)

            # Create field name with parameter name and optional marker
            field_name = nodes.field_name("")
            self.format_optional_parameter(
                field_name,
                param["name"],
                param.get("optional", False),
                in_signature=False,
            )

            field.append(field_name)

            # Create field body with type and description
            field_body = nodes.field_body()
            field.append(field_body)

            # Create paragraph for type and description in a single line
            para = nodes.paragraph()

            # Add type information inline
            if param.get("type"):
                formatted_type = self.format_parameter_type(
                    param.get("type", "")
                )
                para.append(nodes.emphasis("", formatted_type))
                if param.get("default"):
                    para.append(nodes.Text(f" = {param.get('default')}"))

                # Add a space between type and description
                if param["name"] in documented_params:
                    para.append(nodes.Text(" - "))

            # Add description in the same paragraph
            if param["name"] in documented_params:
                para.append(nodes.Text(documented_params[param["name"]]))

            field_body.append(para)

    def _format_property_common(
        self, prop: Any, parent_name: str | None = None
    ) -> addnodes.desc | None:
        """Format a property as RST.

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

        # Create signature
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = "sig-object ts"
        sig["ids"] = [f"property-{prop_id}"]
        desc += sig

        # Add property name
        sig += addnodes.desc_name("", prop.name)

        # Add optional marker for properties if needed
        if hasattr(prop, "is_optional") and prop.is_optional:
            sig += nodes.Text("?")

        # Add property type
        if prop.type_annotation:
            sig += nodes.Text(": ")
            formatted_type = self.format_parameter_type(prop.type_annotation)
            sig += addnodes.desc_type("", formatted_type)

        # Add content container
        content = addnodes.desc_content()
        desc += content

        # Add property documentation
        if prop.doc_comment and prop.doc_comment.description:
            para = nodes.paragraph()
            para += nodes.Text(prop.doc_comment.description)
            content += para

        return desc

    def _add_examples_section(
        self,
        content: nodes.Element,
        doc_comment: Any,
    ) -> None:
        """Add examples section to documentation content.

        Args:
            content: The content container to add examples to
            doc_comment: The doc comment containing examples

        """
        if not (doc_comment and doc_comment.examples):
            return

        # Use rubric instead of section to exclude from TOC
        examples_rubric = nodes.rubric(text="Examples")
        examples_rubric["classes"] = ["ts-examples"]
        content.append(examples_rubric)

        # Create a literal block with all examples
        example_lines = []
        for example in doc_comment.examples:
            example_lines.extend(example.split("\n"))
            if example != doc_comment.examples[-1]:
                example_lines.append("")  # Add separator between examples

        example_text = "\n".join(example_lines)
        example_node = nodes.literal_block(example_text, example_text)
        example_node["language"] = "typescript"
        example_node["classes"] = ["highlight"]
        content.append(example_node)

    def _register_members_with_domain(
        self,
        parent_name: str,
        methods: list | None = None,
        properties: list | None = None,
        noindex: bool = True,
    ) -> None:
        """Register methods and properties with the domain.

        Args:
            parent_name: Name of the parent class/interface
            methods: List of methods to register
            properties: List of properties to register
            noindex: Whether to exclude from TOC (default True for members)

        """
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
