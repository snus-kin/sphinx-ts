"""TypeScript Auto-Directives.

Provides auto-documentation directives for TypeScript code similar to autodoc.
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

from .parser import (
    TSClass,
    TSDocComment,
    TSInterface,
    TSMethod,
    TSParser,
    TSProperty,
    TSValueParser,
    TSVariable,
)

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
        src_dirs = self.config.ts_sphinx_src_dirs or ["."]
        exclude_patterns = self.config.ts_sphinx_exclude_patterns or []

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
                            # Register this object with the domain for cross-referencing
                            self._register_object_with_domain(
                                obj, object_type, self.env.docname
                            )
                            return obj_data
                        if obj.name.lower() == object_name.lower():
                            # Try case-insensitive match if exact match fails
                            obj_data = {
                                "object": obj,
                                "file_path": file_path,
                                "parsed_data": parsed_data,
                            }
                            # Register this object with the domain for cross-referencing
                            self._register_object_with_domain(
                                obj, object_type, self.env.docname
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

        This is a shared method for displaying return information consistently across
        different TypeScript objects (functions, methods, variables). It handles both
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
        if method.doc_comment and method.doc_comment.examples:
            example_lines = self._format_examples(method.doc_comment)
            if example_lines:
                # Convert RST lines to docutils nodes
                examples_rubric = nodes.rubric(text="Examples")
                content.append(examples_rubric)

                # Create a literal block with all examples
                example_text = "\n".join(
                    line.removeprefix("   ") for line in example_lines[3:-1]
                )
                example_node = nodes.literal_block(example_text, example_text)
                example_node["language"] = "typescript"
                example_node["classes"] = ["highlight"]
                content.append(example_node)

        return desc

    def _add_method_description(
        self, content: addnodes.desc_content, method: TSMethod
    ) -> None:
        """Add method description only (no parameters, returns, or examples)."""
        if method.doc_comment and method.doc_comment.description:
            desc_para = nodes.paragraph()
            desc_para.append(nodes.Text(method.doc_comment.description))
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
        self, prop: TSProperty, parent_name: str | None = None
    ) -> addnodes.desc | None:
        """Format a property as RST.

        This shared method can be used by both class and interface directives.

        Args:
            prop: The property to format
            parent_name: Optional parent class/interface name

        Returns:
            A formatted property description (not a section to avoid TOC entries)

        """
        prop_id = f"{parent_name}.{prop.name}" if parent_name else prop.name

        # Create property description directly (no section wrapper)
        desc = addnodes.desc(
            domain="ts",
            objtype="attribute",
            noindex=True,  # Don't index this in the global index
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
        if prop.doc_comment:
            if prop.doc_comment.description:
                para = nodes.paragraph()
                para += nodes.Text(prop.doc_comment.description)
                content += para

        return desc


class TSAutoClassDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript classes."""

    def run(self) -> list[nodes.Node]:
        """Run the directive."""
        class_name = self.arguments[0]

        return self._process_class(class_name)

    def _process_class(self, class_name: str) -> list[nodes.Node]:
        """Process a TypeScript class."""
        # Find the class in source files
        result = self.find_object_in_files(class_name, "class")
        if not result:
            logger.warning("Could not find TypeScript class: %s", class_name)
            return []

        ts_class: TSClass = result["object"]
        file_path = result["file_path"]

        # Register the class with the TypeScript domain
        self._register_object_with_domain("class", class_name, self.env.docname)

        # Register methods and properties but with noindex=True to exclude from TOC
        if ts_class.methods:
            for method in ts_class.methods:
                if method.name:
                    qualified_name = f"{class_name}.{method.name}"
                    self._register_object_with_domain(
                        "method", qualified_name, self.env.docname, noindex=True
                    )

        if ts_class.properties:
            for prop in ts_class.properties:
                if prop.name:
                    qualified_name = f"{class_name}.{prop.name}"
                    self._register_object_with_domain(
                        "property",
                        qualified_name,
                        self.env.docname,
                        noindex=True,
                    )

        # Register only main class in TOC, not every method and property

        # Create the main class directive
        class_node = nodes.section(ids=[f"class-{class_name}"])

        # Add basic class information
        self._add_class_header(class_node, class_name, ts_class, file_path)

        # Add constructor if present
        self._add_constructor_section(class_node, ts_class)

        # Store class name for later use with methods and properties
        self.current_class_name = class_name

        # Add methods and properties
        self._add_methods_section(class_node, ts_class)
        self._add_properties_section(class_node, ts_class)

        return [class_node]

    def _add_class_header(
        self,
        class_node: nodes.section,
        class_name: str,
        ts_class: TSClass,
        file_path: Path,
    ) -> None:
        """Add class header information."""
        # Create class description
        desc = addnodes.desc(
            domain="ts",
            objtype="class",
            noindex=False,
        )
        desc["ids"] = [f"class-{class_name}"]
        class_node += desc

        # Create class signature
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = "sig-object ts"
        sig["ids"] = [f"class-{class_name}"]
        desc += sig

        # Add class keyword and name
        sig += addnodes.desc_annotation("", "class ")
        sig += addnodes.desc_name("", class_name)

        # Add content container
        content = addnodes.desc_content()
        desc += content

        # Add class documentation
        doc_lines = self.format_doc_comment(ts_class.doc_comment)
        if doc_lines:
            content.extend(self.create_rst_content(doc_lines))

        # Add source file information
        source_info = nodes.paragraph("")
        source_info += nodes.emphasis("", f"Source: {file_path.name}")
        content += source_info

    def _add_constructor_section(
        self, class_node: nodes.section, ts_class: TSClass
    ) -> None:
        """Add constructor section if present."""
        if ts_class.constructor:
            constructor_section = self._format_method(
                ts_class.constructor, "Constructor"
            )
            if constructor_section:
                class_node.append(constructor_section)

    def _add_methods_section(
        self, class_node: nodes.section, ts_class: TSClass
    ) -> None:
        """Add methods section if present."""
        if ts_class.methods:
            methods_section = nodes.section(ids=["methods"])
            methods_title = nodes.title(text="Methods")
            methods_section.append(methods_title)

            for method in ts_class.methods:
                method_desc = self._format_method(method)
                if method_desc:
                    methods_section.append(method_desc)

            class_node.append(methods_section)

    def _add_properties_section(
        self, class_node: nodes.section, ts_class: TSClass
    ) -> None:
        """Add properties section if present."""
        if ts_class.properties:
            properties_section = nodes.section(ids=["properties"])
            properties_title = nodes.title(text="Properties")
            properties_section.append(properties_title)

            for prop in ts_class.properties:
                prop_desc = self._format_property(prop)
                if prop_desc:
                    properties_section.append(prop_desc)

            class_node.append(properties_section)

    def _format_method(
        self, method: TSMethod, title_override: str | None = None
    ) -> addnodes.desc | None:
        """Format a method as RST."""
        parent_class = getattr(self, "current_class_name", None)
        return self._format_method_common(method, parent_class, title_override)

    def _create_method_signature(self, method: TSMethod) -> str:
        """Create method signature string."""
        signature = method.name
        if method.parameters:
            param_strs = self._format_method_parameters(method.parameters)
            signature += f"({', '.join(param_strs)})"
        else:
            signature += "()"

        if method.return_type:
            signature += f" {self.format_parameter_type(method.return_type, add_colon=True)}"

        return signature

    def _format_method_parameters(self, parameters: list[dict]) -> list[str]:
        """Format method parameters."""
        return [self.format_parameter_string(param) for param in parameters]

    def _format_property(self, prop: TSProperty) -> addnodes.desc | None:
        """Format a property as RST."""
        parent_class = getattr(self, "current_class_name", None)
        return self._format_property_common(prop, parent_class)


class TSAutoInterfaceDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript interfaces."""

    def run(self) -> list[nodes.Node]:
        """Run the interface auto-documentation directive."""
        interface_name = self.arguments[0]
        return self._process_interface(interface_name)

    def _process_interface(self, interface_name: str) -> list[nodes.Node]:
        """Process a TypeScript interface."""
        # Find the interface in source files
        result = self.find_object_in_files(interface_name, "interface")
        if not result:
            logger.warning(
                "Could not find TypeScript interface: %s", interface_name
            )
            return []

        ts_interface: TSInterface = result["object"]
        file_path = result["file_path"]

        # Register the interface with the TypeScript domain using _register_object_with_domain
        self._register_object_with_domain(
            "interface", interface_name, self.env.docname
        )

        # Register methods
        if ts_interface.methods:
            for method in ts_interface.methods:
                if hasattr(method, "name") and method.name:
                    qualified_name = f"{interface_name}.{method.name}"
                    self._register_object_with_domain(
                        "method", qualified_name, self.env.docname
                    )

        # Register properties
        if ts_interface.properties:
            for prop in ts_interface.properties:
                if hasattr(prop, "name") and prop.name:
                    qualified_name = f"{interface_name}.{prop.name}"
                    self._register_object_with_domain(
                        "property", qualified_name, self.env.docname
                    )

        # Create the main interface directive
        interface_node = nodes.section(ids=[f"interface-{interface_name}"])

        # Store interface name for later use with methods and properties
        self.current_interface_name = interface_name

        # Add interface information sections
        self._add_interface_header(
            interface_node, interface_name, ts_interface, file_path
        )
        self._add_interface_methods_section(interface_node, ts_interface)
        self._add_interface_properties_section(interface_node, ts_interface)

        return [interface_node]

    def _add_interface_header(
        self,
        interface_node: nodes.section,
        interface_name: str,
        ts_interface: TSInterface,
        file_path: Path,
    ) -> None:
        """Add interface header information."""
        # Create interface description
        desc = addnodes.desc(
            domain="ts",
            objtype="interface",
            noindex=False,
        )
        desc["ids"] = [f"interface-{interface_name}"]
        interface_node += desc

        # Create interface signature
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = "sig-object ts"
        sig["ids"] = [f"interface-{interface_name}"]
        desc += sig

        # Add interface keyword and name
        sig += addnodes.desc_annotation("", "interface ")
        sig += addnodes.desc_name("", interface_name)

        # Add type parameters if present
        if ts_interface.type_parameters:
            sig += nodes.Text(f"<{', '.join(ts_interface.type_parameters)}>")

        # Add extends clause if present
        if ts_interface.extends:
            sig += nodes.Text(f" extends {', '.join(ts_interface.extends)}")

        # Add content container
        content = addnodes.desc_content()
        desc += content

        # Add interface documentation
        doc_lines = self.format_doc_comment(ts_interface.doc_comment)
        if doc_lines:
            content.extend(self.create_rst_content(doc_lines))

        # Add source file information
        source_info = nodes.paragraph("")
        source_info += nodes.emphasis("", f"Source: {file_path.name}")
        content += source_info

    def _add_interface_methods_section(
        self,
        interface_node: nodes.section,
        ts_interface: TSInterface,
    ) -> None:
        """Add interface methods section."""
        if ts_interface.methods:
            methods_section = nodes.section(ids=["methods"])
            methods_title = nodes.title(text="Methods")
            methods_section.append(methods_title)

            for method in ts_interface.methods:
                method_desc = self._format_method(method)
                if method_desc:
                    methods_section.append(method_desc)

            interface_node.append(methods_section)

    def _add_interface_properties_section(
        self,
        interface_node: nodes.section,
        ts_interface: TSInterface,
    ) -> None:
        """Add interface properties section."""
        if ts_interface.properties:
            props_section = nodes.section(ids=["properties"])
            props_title = nodes.title(text="Properties")
            props_section.append(props_title)

            for prop in ts_interface.properties:
                prop_desc = self._format_property(prop)
                if prop_desc:
                    props_section.append(prop_desc)

            interface_node.append(props_section)

    def _format_method(
        self, method: TSMethod, title_override: str | None = None
    ) -> addnodes.desc | None:
        """Format a method as RST."""
        parent_interface = getattr(self, "current_interface_name", None)
        return self._format_method_common(
            method, parent_interface, title_override
        )

    def _format_property(self, prop: TSProperty) -> addnodes.desc | None:
        """Format a property as RST."""
        parent_interface = getattr(self, "current_interface_name", None)
        return self._format_property_common(prop, parent_interface)


class TSAutoDataDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript variables/constants."""

    def run(self) -> list[nodes.Node]:
        """Run the variable auto-documentation directive."""
        variable_name = self.arguments[0]

        # Find the variable in source files
        result = self.find_object_in_files(variable_name, "variable")

        # If not found as a variable, try to find it as a function
        if not result:
            function_result = self.find_object_in_files(
                variable_name, "function"
            )
            if function_result:
                return self._process_function(function_result, variable_name)

            logger.warning(
                "Could not find TypeScript variable or function: %s",
                variable_name,
            )
            # Try to build the documentation anyway, even if a warning is shown
            # This helps users debug what's happening by providing context
            return []

        ts_variable: TSVariable = result["object"]
        file_path = result["file_path"]

        # Register the variable with the TypeScript domain
        self._register_object_with_domain(
            "variable", variable_name, self.env.docname
        )

        # Create the main variable directive
        var_node = nodes.section(ids=[f"variable-{variable_name}"])

        # Create variable signature for the title - only include name and type
        signature = variable_name
        if ts_variable.type_annotation:
            formatted_type = self.format_parameter_type(
                ts_variable.type_annotation, add_colon=True
            )
            signature += f" {formatted_type}"

        # Add variable title
        title = nodes.title(text=signature)
        var_node.append(title)

        # Add variable kind (const, let, var) as a subtitle
        kind_para = nodes.paragraph(classes=["ts-variable-kind"])
        kind_para.append(nodes.emphasis(text=f"{ts_variable.kind}"))
        var_node.append(kind_para)

        # Add variable documentation (description for the whole variable)
        # But exclude @param tags which will be shown in the value table
        doc_lines = []
        if ts_variable.doc_comment:
            # Extract only the description and non-param documentation
            if ts_variable.doc_comment.description:
                doc_lines.extend(
                    ts_variable.doc_comment.description.split("\n")
                )
                doc_lines.append("")

            # Skip returns in doc comment since we'll handle it separately
            # (We handle returns separately with format_returns_section)

            if ts_variable.doc_comment.examples:
                doc_lines.extend([".. rubric:: Examples", ""])
                # Use only one code block for all examples to prevent duplication
                doc_lines.append(".. code-block:: typescript")
                doc_lines.append("")
                for example in ts_variable.doc_comment.examples:
                    doc_lines.extend(
                        f"   {line}" for line in example.split("\n")
                    )
                    if example != ts_variable.doc_comment.examples[-1]:
                        doc_lines.append(
                            "   "
                        )  # Add separator between examples
                doc_lines.append("")

            if ts_variable.doc_comment.deprecated:
                doc_lines.extend(
                    [
                        ".. warning::",
                        "",
                        f"   **Deprecated**: {ts_variable.doc_comment.deprecated}",
                        "",
                    ]
                )

            if ts_variable.doc_comment.since:
                doc_lines.extend(
                    [
                        ".. note::",
                        "",
                        f"   Available since version {ts_variable.doc_comment.since}",
                        "",
                    ]
                )

        if doc_lines:
            var_node.extend(self.create_rst_content(doc_lines))

        # Add returns section using the shared method
        if ts_variable.doc_comment and ts_variable.doc_comment.returns:
            self.format_returns_section(var_node, ts_variable.doc_comment)

        # Add source file information
        source_info = nodes.paragraph()
        source_info.append(nodes.emphasis(text=f"Source: {file_path.name}"))
        var_node.append(source_info)

        # Add value if available
        if ts_variable.value:
            value_section = nodes.section(ids=[f"{variable_name}-value"])
            value_section.append(nodes.rubric(text="Value"))

            # Parse the value to determine how to display it
            value_data = TSValueParser.parse_value(ts_variable.value)

            # For const values (which are likely to have complex properties), use a code block
            if ts_variable.kind == "const" and (
                value_data["type"] == "object"
                or value_data["type"].endswith("[]")
                or "{" in ts_variable.value
            ):
                # Add a prefix to show this is a constant declaration
                declaration = f"const {ts_variable.name} = "

                # Format the value with proper syntax highlighting
                formatted_value = TSValueParser.format_value(ts_variable.value)

                # Combine the declaration and value
                full_code = f"{declaration}{formatted_value};"

                code_block = nodes.literal_block(text=full_code)
                code_block["language"] = "typescript"
                code_block["classes"] = ["highlight"]
                value_section.append(code_block)

                # Add property descriptions after the code block if available
                if ts_variable.doc_comment and ts_variable.doc_comment.params:
                    props_section = nodes.section()
                    props_section.append(
                        nodes.rubric(text="Property Descriptions")
                    )

                    # Create a definition list for properties
                    prop_list = nodes.definition_list()
                    prop_list["classes"] = ["ts-property-descriptions"]

                    # Sort properties alphabetically for easier reference
                    sorted_props = sorted(
                        ts_variable.doc_comment.params.items()
                    )

                    for prop_name, prop_desc in sorted_props:
                        if prop_desc:
                            term_item = nodes.term()
                            term_item += nodes.literal(text=prop_name)

                            def_item = nodes.definition()
                            def_item += nodes.paragraph(text=prop_desc)

                            list_item = nodes.definition_list_item()
                            list_item += term_item
                            list_item += def_item
                            prop_list += list_item

                    if len(prop_list.children) > 0:
                        props_section.append(prop_list)
                        value_section.append(props_section)
            else:
                # Use table for simpler values
                value_table = self._create_value_table(ts_variable)
                if value_table:
                    value_section.append(value_table)
                else:
                    # Fallback to simple display if table creation fails
                    value_para = nodes.paragraph()
                    value_code = nodes.literal(text=ts_variable.value)
                    value_para += value_code
                    value_section.append(value_para)

            var_node.append(value_section)

        return [var_node]

    def _create_value_table(
        self, ts_variable: TSVariable
    ) -> nodes.table | None:
        """Create a table showing the variable value with type info and descriptions."""
        # Create a table for the value
        table = nodes.table(classes=["variable-value-table"])
        tgroup = nodes.tgroup(cols=4)
        table += tgroup

        # Add column specs - name/field, type, value, description
        tgroup.append(nodes.colspec(colwidth=15))
        tgroup.append(nodes.colspec(colwidth=15))
        tgroup.append(nodes.colspec(colwidth=25))
        tgroup.append(nodes.colspec(colwidth=45))

        # Create table header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        header_row.append(nodes.entry("", nodes.paragraph(text="Field")))
        header_row.append(nodes.entry("", nodes.paragraph(text="Type")))
        header_row.append(nodes.entry("", nodes.paragraph(text="Value")))
        header_row.append(nodes.entry("", nodes.paragraph(text="Description")))
        thead.append(header_row)

        # Create table body
        tbody = nodes.tbody()
        tgroup += tbody

        # Get documentation for fields from JSDoc comments
        field_docs = {}
        if ts_variable.doc_comment and ts_variable.doc_comment.params:
            field_docs = ts_variable.doc_comment.params

        # If value is None, return None
        if ts_variable.value is None:
            return None

        # Use the TSValueParser to parse the value
        value_data = TSValueParser.parse_value(ts_variable.value)

        # Check if it's a const with a complex value - we'll use a code block instead
        if ts_variable.kind == "const" and (
            (value_data["type"] == "object" and value_data["properties"])
            or value_data["type"].endswith("[]")
            or "{" in ts_variable.value
        ):
            return None

            # For objects, render them in a table
            # Add rows for each property in the object
            for prop in value_data["properties"]:
                field_row = nodes.row()

                # Field name cell
                name_cell = nodes.entry()
                name_para = nodes.paragraph()
                name_para += nodes.literal(text=prop["key"])
                name_cell += name_para
                field_row.append(name_cell)

                # Type cell
                type_cell = nodes.entry()
                if prop["type"] != "unknown":
                    type_para = nodes.paragraph()
                    type_para += nodes.literal(text=prop["type"])
                    type_cell += type_para
                field_row.append(type_cell)

                # Value cell
                value_cell = nodes.entry()
                value_para = nodes.paragraph()
                value_para += nodes.literal(text=prop["value"])
                value_cell += value_para
                field_row.append(value_cell)

                # Description cell
                desc_cell = nodes.entry()
                if (
                    prop["key"] in field_docs
                    and field_docs[prop["key"]] is not None
                ):
                    desc_para = nodes.paragraph()
                    desc_para += nodes.Text(str(field_docs[prop["key"]]))
                    desc_cell += desc_para
                field_row.append(desc_cell)

                tbody.append(field_row)

            return table

        # For simple values, create a single row
        value_row = nodes.row()

        # Value name cell
        name_cell = nodes.entry()
        name_cell += nodes.paragraph(text="(value)")
        value_row.append(name_cell)

        # Value type cell
        type_cell = nodes.entry()
        if ts_variable.type_annotation:
            type_para = nodes.paragraph()
            type_para += nodes.literal(
                text=self.format_type_annotation(ts_variable.type_annotation)
            )
            type_cell += type_para
        elif value_data["type"] != "unknown":
            type_para = nodes.paragraph()
            type_para += nodes.literal(text=value_data["type"])
            type_cell += type_para
        value_row.append(type_cell)

        # Value content cell - the actual value
        content_cell = nodes.entry()
        value_text = ts_variable.value if ts_variable.value is not None else ""

        # Format the value appropriately
        if value_data["type"] in ["object", "array"]:
            # Format complex values with syntax highlighting
            formatted_value = TSValueParser.format_value(value_text)
            code_block = nodes.literal_block(text=formatted_value)
            code_block["language"] = "typescript"
            code_block["classes"] = ["highlight"]
            content_cell += code_block
        else:
            content_para = nodes.paragraph()
            content_para += nodes.literal(text=value_text)
            content_cell += content_para

        value_row.append(content_cell)

        # Value description cell
        desc_cell = nodes.entry()
        if ts_variable.doc_comment and ts_variable.doc_comment.description:
            desc_para = nodes.paragraph()
            desc_text = str(ts_variable.doc_comment.description or "")
            desc_para += nodes.Text(desc_text)
            desc_cell += desc_para
        value_row.append(desc_cell)

        tbody.append(value_row)

        return table

    def _process_function(
        self, result: dict[str, Any], function_name: str
    ) -> list[nodes.Node]:
        """Process a TypeScript function and render it as data."""
        ts_function = result["object"]
        file_path = result["file_path"]

        # Register the function with the TypeScript domain
        self._register_object_with_domain(
            "function", function_name, self.env.docname
        )

        # Create the main function directive
        # Register the function with the domain
        self._register_object_with_domain(
            "function", function_name, self.env.docname
        )

        func_node = addnodes.desc(
            domain="ts",
            objtype="function",
            noindex=False,
        )
        func_node["ids"] = [f"function-{function_name}"]

        # Create function signature
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = "sig-object ts"
        sig["ids"] = [f"function-{function_name}"]
        func_node += sig

        # Add function name
        sig += addnodes.desc_name("", function_name)

        # Add parameter list
        paramlist = addnodes.desc_parameterlist()
        sig += paramlist

        # Add parameters to signature
        if ts_function.parameters:
            for param in ts_function.parameters:
                parameter = addnodes.desc_parameter("", "")
                paramlist += parameter

                # Use the shared parameter formatting helper
                self.format_parameter_nodes(parameter, param)

        # Add return type
        if ts_function.return_type:
            sig += nodes.Text(": ")
            formatted_type = self.format_parameter_type(ts_function.return_type)
            sig += addnodes.desc_type("", formatted_type)

        # Add content container
        content = addnodes.desc_content()
        func_node += content

        # Add function documentation
        if ts_function.doc_comment and ts_function.doc_comment.description:
            desc_para = nodes.paragraph()
            desc_para.append(nodes.Text(ts_function.doc_comment.description))
            content.append(desc_para)

        # Add parameter information
        if ts_function.parameters:
            # Extract documented parameters from doc_comment if it exists
            documented_params = {}
            if ts_function.doc_comment and ts_function.doc_comment.params:
                documented_params = ts_function.doc_comment.params

            # Add a rubric for parameters
            param_rubric = nodes.rubric(text="Parameters")
            content.append(param_rubric)

            # Create field list for parameters
            field_list = nodes.field_list()
            content.append(field_list)

            # Add parameters as field items
            for param in ts_function.parameters:
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

                # Create paragraph for type information
                type_para = nodes.paragraph()
                if param.get("type"):
                    type_para.append(nodes.strong("Type: "))
                    formatted_type = self.format_parameter_type(
                        param.get("type")
                    )
                    type_para.append(nodes.literal("", formatted_type))
                    if param.get("default"):
                        type_para.append(
                            nodes.Text(f", default: {param.get('default')}")
                        )
                    field_body.append(type_para)

                # Create paragraph for description
                if param["name"] in documented_params:
                    desc_para = nodes.paragraph()
                    desc_para.append(
                        nodes.Text(documented_params[param["name"]])
                    )
                    field_body.append(desc_para)

        # Add returns documentation using the shared method
        if ts_function.doc_comment and ts_function.doc_comment.returns:
            self.format_returns_section(
                content, ts_function.doc_comment, ts_function.return_type
            )

        # Add examples documentation
        if ts_function.doc_comment and ts_function.doc_comment.examples:
            example_lines = self._format_examples(ts_function.doc_comment)
            if example_lines:
                # Convert RST lines to docutils nodes
                examples_rubric = nodes.rubric(text="Examples")
                content.append(examples_rubric)

                # Create a literal block with all examples
                example_text = "\n".join(
                    line.removeprefix("   ") for line in example_lines[3:-1]
                )
                example_node = nodes.literal_block(example_text, example_text)
                example_node["language"] = "typescript"
                example_node["classes"] = ["highlight"]
                content.append(example_node)

        # Add function kind as a subtitle
        kind_para = nodes.paragraph("", classes=["ts-function-kind"])
        kind_para += nodes.emphasis("", "function")
        func_node.append(kind_para)

        # Add function documentation
        doc_lines = self.format_doc_comment(
            ts_function.doc_comment, skip_examples=True
        )
        if doc_lines:
            func_node.extend(self.create_rst_content(doc_lines))

        # Add source file information
        source_info = nodes.paragraph("")
        source_info += nodes.emphasis("", f"Source: {file_path.name}")
        func_node.append(source_info)

        # Add parameters section if available
        # Parameters already added in the main function processing

        # We already handle returns in format_returns_section above,
        # so we don't need this separate section anymore.
        # This ensures consistent returns formatting across all TypeScript objects.

        return [func_node]
