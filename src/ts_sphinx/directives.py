"""TypeScript Auto-Directives.

Provides auto-documentation directives for TypeScript code similar to autodoc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from docutils import nodes
from docutils.core import publish_doctree
from docutils.parsers.rst import directives
from docutils.utils import SystemMessage
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

from .parser import (
    TSClass,
    TSDocComment,
    TSInterface,
    TSMethod,
    TSParser,
    TSProperty,
    TSVariable,
)

logger = logging.getLogger(__name__)


class TSAutoDirective(SphinxDirective):
    """Base class for TypeScript auto-directives."""

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec: dict[str, Callable[[str | None], str | None]] = {
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
        "synopsis": directives.unchanged,
        "platform": directives.unchanged,
        "deprecated": directives.flag,
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

                # Search in the appropriate category
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
                    if hasattr(obj, "name") and obj.name == object_name:
                        return {
                            "object": obj,
                            "file_path": file_path,
                            "parsed_data": parsed_data,
                        }

            except Exception as e:  # noqa: BLE001, PERF203
                logger.warning("Failed to parse %s: %s", file_path, e)
                continue

        return None

    def format_doc_comment(self, doc_comment: TSDocComment | None) -> list[str]:
        """Format a JSDoc comment as reStructuredText."""
        if not doc_comment:
            return []

        lines = []

        # Add description
        if doc_comment.description:
            lines.extend(doc_comment.description.split("\n"))
            lines.append("")

        # Add parameters
        lines.extend(self._format_parameters(doc_comment))

        # Add return information
        lines.extend(self._format_returns(doc_comment))

        # Add examples
        lines.extend(self._format_examples(doc_comment))

        # Add other tags
        lines.extend(self._format_other_tags(doc_comment))

        return lines

    def _format_parameters(self, doc_comment: TSDocComment) -> list[str]:
        """Format parameter documentation."""
        if not doc_comment.params:
            return []

        lines = [":Parameters:"]
        for param_name, param_desc in doc_comment.params.items():
            if param_desc:
                lines.append(f"    * ``{param_name}`` -- {param_desc}")
            else:
                lines.append(f"    * ``{param_name}``")
        lines.append("")
        return lines

    def _format_returns(self, doc_comment: TSDocComment) -> list[str]:
        """Format return documentation."""
        if not doc_comment.returns:
            return []
        return [f":Returns: {doc_comment.returns}", ""]

    def _format_examples(self, doc_comment: TSDocComment) -> list[str]:
        """Format example documentation."""
        lines = []
        for example in doc_comment.examples:
            lines.append("Example ::")
            lines.append("")
            lines.extend(f"    {line}" for line in example.split("\n"))
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
        if cleaned.startswith(":"):
            cleaned = cleaned[1:].strip()

        return cleaned

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

        # Create the main class directive
        class_node = nodes.section(ids=[f"class-{class_name}"])

        # Add basic class information
        self._add_class_header(class_node, class_name, ts_class, file_path)

        # Add constructor if present
        self._add_constructor_section(class_node, ts_class)

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
        # Add class title
        title = nodes.title(text=f"class {class_name}")
        class_node.append(title)

        # Add class documentation
        doc_lines = self.format_doc_comment(ts_class.doc_comment)
        if doc_lines:
            class_node.extend(self.create_rst_content(doc_lines))

        # Add source file information
        source_info = nodes.paragraph()
        source_info.append(nodes.emphasis(text=f"Source: {file_path.name}"))
        class_node.append(source_info)

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
                method_section = self._format_method(method)
                if method_section:
                    methods_section.append(method_section)

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
                prop_section = self._format_property(prop)
                if prop_section:
                    properties_section.append(prop_section)

            class_node.append(properties_section)

    def _format_method(
        self,
        method: TSMethod,
        title_override: str | None = None,
    ) -> nodes.section | None:
        """Format a method as RST."""
        method_section = nodes.section(ids=[f"method-{method.name}"])

        # Create method signature and title
        signature = self._create_method_signature(method)
        title_text = title_override or method.name
        title = nodes.title(
            text=f"{title_text}{signature[len(method.name) :]}"
        )
        method_section.append(title)

        # Add method documentation
        self._add_method_documentation(method_section, method)

        # Add parameter information
        self._add_parameter_list(method_section, method)

        return method_section

    def _create_method_signature(self, method: TSMethod) -> str:
        """Create method signature string."""
        signature = method.name
        if method.parameters:
            param_strs = self._format_method_parameters(method.parameters)
            signature += f"({', '.join(param_strs)})"
        else:
            signature += "()"

        if method.return_type:
            signature += f"{method.return_type}"

        return signature

    def _format_method_parameters(self, parameters: list[dict]) -> list[str]:
        """Format method parameters."""
        param_strs = []
        for param in parameters:
            param_str = param["name"]
            if param.get("type"):
                param_str += f"{param['type']}"
            if param.get("optional"):
                param_str += "?"
            if param.get("default"):
                param_str += f" = {param['default']}"
            param_strs.append(param_str)
        return param_strs

    def _add_method_documentation(
        self, method_section: nodes.section, method: TSMethod
    ) -> None:
        """Add method documentation to section."""
        doc_lines = self.format_doc_comment(method.doc_comment)
        if doc_lines:
            method_section.extend(self.create_rst_content(doc_lines))

    def _add_parameter_list(
        self, method_section: nodes.section, method: TSMethod
    ) -> None:
        """Add parameter list to method section."""
        if not method.parameters:
            return

        param_list = nodes.bullet_list()
        for param in method.parameters:
            item = nodes.list_item()
            # TODO fix this to make it a bit nicer
            param_text = f" ``{param['name']}``"
            if param.get("type"):
                param_text += f"{param['type']}"
            if param.get("optional"):
                param_text += " - optional"

            para = nodes.paragraph()
            para.append(nodes.raw(text=param_text, format="html"))
            item.append(para)
            param_list.append(item)

        method_section.append(param_list)

    def _format_property(self, prop: TSProperty) -> nodes.section | None:
        """Format a property as RST."""
        prop_section = nodes.section(ids=[f"property-{prop.name}"])

        # Create property signature
        signature = prop.name
        if prop.type_annotation:
            type_annotation = self.format_type_annotation(prop.type_annotation)
            signature += f": {type_annotation}"

        # Add property title
        title = nodes.title(text=signature)
        prop_section.append(title)

        # Add property documentation
        doc_lines = self.format_doc_comment(prop.doc_comment)
        if doc_lines:
            prop_section.extend(self.create_rst_content(doc_lines))

        return prop_section


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

        # Create the main interface directive
        interface_node = nodes.section(ids=[f"interface-{interface_name}"])

        # Add interface information sections
        self._add_interface_header(
            interface_node, interface_name, ts_interface, file_path
        )
        self._add_interface_methods_section(
            interface_node, interface_name, ts_interface
        )
        self._add_interface_properties_section(
            interface_node, interface_name, ts_interface
        )

        return [interface_node]

    def _add_interface_header(
        self,
        interface_node: nodes.section,
        interface_name: str,
        ts_interface: TSInterface,
        file_path: Path,
    ) -> None:
        """Add interface header information."""
        # Add interface title
        title = nodes.title(text=f"interface {interface_name}")
        interface_node.append(title)

        # Add interface documentation
        doc_lines = self.format_doc_comment(ts_interface.doc_comment)
        if doc_lines:
            interface_node.extend(self.create_rst_content(doc_lines))

        # Add source file information
        source_info = nodes.paragraph()
        source_info.append(nodes.emphasis(text=f"Source: {file_path.name}"))
        interface_node.append(source_info)

        # Add interface signature
        signature = interface_name
        if ts_interface.type_parameters:
            signature += f"<{', '.join(ts_interface.type_parameters)}>"
        if ts_interface.extends:
            signature += f" extends {', '.join(ts_interface.extends)}"

        signature_para = nodes.paragraph()
        signature_para.append(nodes.strong(text=signature))
        interface_node.append(signature_para)

    def _add_interface_methods_section(
        self,
        interface_node: nodes.section,
        interface_name: str,
        ts_interface: TSInterface,
    ) -> None:
        """Add interface methods section."""
        if ts_interface.methods:
            methods_section = nodes.section(ids=[f"{interface_name}-methods"])
            methods_title = nodes.title(text="Methods")
            methods_section.append(methods_title)

            for method in ts_interface.methods:
                method_section = self._format_interface_method(method)
                if method_section:
                    methods_section.append(method_section)

            interface_node.append(methods_section)

    def _add_interface_properties_section(
        self,
        interface_node: nodes.section,
        interface_name: str,
        ts_interface: TSInterface,
    ) -> None:
        """Add interface properties section."""
        if ts_interface.properties:
            props_section = nodes.section(ids=[f"{interface_name}-properties"])
            props_title = nodes.title(text="Properties")
            props_section.append(props_title)

            for prop in ts_interface.properties:
                prop_section = self._format_property(prop)
                if prop_section:
                    props_section.append(prop_section)

            interface_node.append(props_section)

    def _format_interface_method(
        self, method: TSMethod
    ) -> nodes.section | None:
        """Format an interface method signature as RST."""
        return self._format_method(method)

    def _format_interface_method_detailed(
        self, method: TSMethod
    ) -> nodes.section | None:
        """Format a method signature as RST."""
        method_section = nodes.section(ids=[f"method-{method.name}"])

        # Create method signature
        signature = method.name
        if method.parameters:
            param_strs = []
            for param in method.parameters:
                param_str = param["name"]
                if param.get("type"):
                    param_str += f": {param['type']}"
                if param.get("optional"):
                    param_str += "?"
                param_strs.append(param_str)
            signature += f"({', '.join(param_strs)})"
        else:
            signature += "()"

        if method.return_type:
            signature += f"{method.return_type}"

        # Add method title
        title = nodes.title(text=signature)
        method_section.append(title)

        # Add method documentation
        doc_lines = self.format_doc_comment(method.doc_comment)
        if doc_lines:
            method_section.extend(self.create_rst_content(doc_lines))

        return method_section

    def _format_property(self, prop: TSProperty) -> nodes.section | None:
        """Format a property signature as RST."""
        prop_section = nodes.section(ids=[f"property-{prop.name}"])

        # Create property signature
        signature = prop.name
        if prop.is_optional:
            signature += "?"
        if prop.type_annotation:
            type_annotation = self.format_type_annotation(prop.type_annotation)
            signature += f": {type_annotation}"

        # Add property title
        title = nodes.title(text=signature)
        prop_section.append(title)

        # Add property documentation
        doc_lines = self.format_doc_comment(prop.doc_comment)
        if doc_lines:
            prop_section.extend(self.create_rst_content(doc_lines))

        return prop_section


class TSAutoDataDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript variables/constants."""

    def run(self) -> list[nodes.Node]:
        """Run the variable auto-documentation directive."""
        variable_name = self.arguments[0]

        # Find the variable in source files
        result = self.find_object_in_files(variable_name, "variable")
        if not result:
            logger.warning(
                "Could not find TypeScript variable: %s", variable_name
            )
            return []

        ts_variable: TSVariable = result["object"]
        file_path = result["file_path"]

        # Create the main variable directive
        var_node = nodes.section(ids=[f"variable-{variable_name}"])

        # Create variable signature
        signature = f"{ts_variable.kind} {variable_name}"
        if ts_variable.type_annotation:
            type_annotation = self.format_type_annotation(
                ts_variable.type_annotation
            )
            signature += f": {type_annotation}"
        if ts_variable.value:
            signature += f" = {ts_variable.value}"

        # Add variable title
        title = nodes.title(text=signature)
        var_node.append(title)

        # Add variable documentation
        doc_lines = self.format_doc_comment(ts_variable.doc_comment)
        if doc_lines:
            var_node.extend(self.create_rst_content(doc_lines))

        # Add source file information
        source_info = nodes.paragraph()
        source_info.append(nodes.emphasis(text=f"Source: {file_path.name}"))
        var_node.append(source_info)

        # Add type and value information
        if ts_variable.type_annotation or ts_variable.value:
            info_section = nodes.section(ids=[f"{variable_name}-info"])

            if ts_variable.type_annotation:
                type_para = nodes.paragraph()
                type_para.append(nodes.strong(text="Type: "))
                type_para.append(
                    nodes.literal(
                        text=self.format_type_annotation(
                            ts_variable.type_annotation
                        ),
                    ),
                )
                info_section.append(type_para)

            if ts_variable.value:
                value_para = nodes.paragraph()
                value_para.append(nodes.strong(text="Value: "))
                value_para.append(nodes.literal(text=ts_variable.value))
                info_section.append(value_para)

            var_node.append(info_section)

        return [var_node]
