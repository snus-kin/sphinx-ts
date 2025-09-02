"""TypeScript Parser Module.

Uses Tree-sitter to parse TypeScript files and extract information.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import tree_sitter
from tree_sitter import Language, Parser
from tree_sitter_typescript import language_typescript


class TSDocComment:
    """Represents a TypeScript JSDoc comment."""

    def __init__(self, text: str) -> None:
        """Initialize a TypeScript JSDoc comment.

        Args:
            text: The raw JSDoc comment text

        """
        self.text = text
        self.description = ""
        self.params: dict[str, str] = {}
        self.returns: str | None = None
        self.examples: list[str] = []
        self.deprecated: str | None = None
        self.since: str | None = None
        self.tags: dict[str, str] = {}

        self._parse()

    def _parse(self) -> None:
        """Parse JSDoc comment text."""
        # Remove comment markers
        lines = []
        for original_line in self.text.split("\n"):
            processed_line = original_line.strip()
            if processed_line.startswith("/**"):
                processed_line = processed_line[3:].strip()
            elif processed_line.startswith("*/"):
                continue
            elif processed_line.startswith("*"):
                processed_line = processed_line[1:].strip()
            lines.append(processed_line)

        content = "\n".join(lines).strip()

        # Split into description and tags
        parts = re.split(r"\n\s*@", content, maxsplit=1)
        self.description = parts[0].strip()

        if len(parts) > 1:
            tag_content = parts[1]
            self._parse_tags("@" + tag_content)

    def _parse_tags(self, tag_content: str) -> None:
        """Parse JSDoc tags."""
        tags = re.findall(
            r"@(\w+)(?:\s+([^@]+))?",
            tag_content,
            re.MULTILINE | re.DOTALL,
        )

        for tag_name, original_tag_value in tags:
            tag_value = original_tag_value.strip() if original_tag_value else ""

            if tag_name == "param":
                # Parse @param {type} name description
                match = re.match(
                    r"(?:\{([^}]+)\})?\s*(\w+)(?:\s+(.+))?",
                    tag_value,
                    re.DOTALL,
                )
                if match:
                    param_type, param_name, param_desc = match.groups()
                    self.params[param_name] = param_desc or ""
            elif tag_name in {"returns", "return"}:
                self.returns = tag_value
            elif tag_name == "example":
                # TODO strip out markdown in tag in a better way
                tag_value = tag_value.replace("```typescript", "").replace("```", "")
                self.examples.append(tag_value)
            elif tag_name == "deprecated":
                self.deprecated = tag_value
            elif tag_name == "since":
                self.since = tag_value
            else:
                self.tags[tag_name] = tag_value


class TSMember:
    """Base class for TypeScript members (methods, properties, etc.)."""

    def __init__(self, name: str, kind: str) -> None:
        """Initialize a TypeScript member.

        Args:
            name: The name of the member
            kind: The kind of member (method, property, etc.)

        """
        self.name = name
        self.kind = kind  # 'method', 'property', 'constructor', etc.
        self.modifiers: list[str] = []
        self.type_annotation: str | None = None
        self.doc_comment: TSDocComment | None = None
        self.is_static = False
        self.is_private = False
        self.is_protected = False
        self.is_readonly = False
        self.is_optional = False


class TSMethod(TSMember):
    """Represents a TypeScript method."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript method.

        Args:
            name: The name of the method

        """
        super().__init__(name, "method")
        self.parameters: list[dict[str, Any]] = []
        self.return_type: str | None = None
        self.is_async = False
        self.is_generator = False


class TSProperty(TSMember):
    """Represents a TypeScript property."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript property.

        Args:
            name: The name of the property

        """
        super().__init__(name, "property")
        self.default_value: str | None = None


class TSClass:
    """Represents a TypeScript class."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript class.

        Args:
            name: The name of the class

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.extends: str | None = None
        self.implements: list[str] = []
        self.type_parameters: list[str] = []
        self.methods: list[TSMethod] = []
        self.properties: list[TSProperty] = []
        self.constructor: TSMethod | None = None
        self.is_abstract = False
        self.is_export = False
        self.modifiers: list[str] = []


class TSInterface:
    """Represents a TypeScript interface."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript interface.

        Args:
            name: The name of the interface

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.extends: list[str] = []
        self.type_parameters: list[str] = []
        self.methods: list[TSMethod] = []
        self.properties: list[TSProperty] = []
        self.is_export = False


class TSVariable:
    """Represents a TypeScript variable/constant."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript variable.

        Args:
            name: The name of the variable

        """
        self.name = name
        self.doc_comment: TSDocComment | None = None
        self.type_annotation: str | None = None
        self.value: str | None = None
        self.kind = "let"  # 'let', 'const', 'var'
        self.is_export = False


class TSParser:
    """TypeScript parser using Tree-sitter."""

    def __init__(self) -> None:
        """Initialize the TypeScript parser with Tree-sitter."""
        # Initialize Tree-sitter
        self.parser = Parser()
        language_capsule = language_typescript()
        self.language = Language(language_capsule)
        self.parser.language = self.language

    def parse_file(self, file_path: str | Path) -> dict[str, Any]:
        """Parse a TypeScript file and return extracted information."""
        file_path = Path(file_path)

        # Return empty result if parser is not available
        if self.parser is None:
            return {
                "classes": [],
                "interfaces": [],
                "variables": [],
                "functions": [],
                "file_path": str(file_path),
            }

        with Path(file_path).open("rb") as f:
            source_code = f.read()

        tree = self.parser.parse(source_code)

        result = {
            "classes": [],
            "interfaces": [],
            "variables": [],
            "functions": [],
            "file_path": str(file_path),
        }

        if tree and tree.root_node:
            self._traverse_node(tree.root_node, source_code, result)
        return result

    def _traverse_node(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
        result: dict[str, Any],
    ) -> None:
        """Recursively traverse the AST and extract information."""
        if node.type == "class_declaration":
            class_obj = self._parse_class(node, source_code)
            if class_obj:
                result["classes"].append(class_obj)

        elif node.type == "interface_declaration":
            interface_obj = self._parse_interface(node, source_code)
            if interface_obj:
                result["interfaces"].append(interface_obj)

        elif node.type == "variable_declaration":
            variables = self._parse_variable_declaration(node, source_code)
            result["variables"].extend(variables)

        elif node.type == "function_declaration":
            function_obj = self._parse_function(node, source_code)
            if function_obj:
                result["functions"].append(function_obj)

        # Recursively traverse child nodes
        for child in node.children:
            self._traverse_node(child, source_code, result)

    def _get_node_text(self, node: tree_sitter.Node, source_code: bytes) -> str:
        """Get the text content of a node."""
        return source_code[node.start_byte : node.end_byte].decode("utf-8")

    def _find_doc_comment(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSDocComment | None:
        """Find JSDoc comment preceding a node."""
        # Look for comment nodes before this node
        current = node.prev_sibling
        while current:
            if current.type == "comment":
                text = self._get_node_text(current, source_code)
                if text.strip().startswith("/**"):
                    return TSDocComment(text)
            elif current.type not in ["comment", "export_statement"]:
                break
            current = current.prev_sibling
        return None

    def _parse_class(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSClass | None:
        """Parse a class declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        class_name = self._get_node_text(name_node, source_code)
        class_obj = TSClass(class_name)

        # Get documentation comment
        class_obj.doc_comment = self._find_doc_comment(node, source_code)

        # Parse class body
        body_node = node.child_by_field_name("body")
        if body_node:
            self._parse_class_body(body_node, source_code, class_obj)

        # Check for export modifier
        parent = node.parent
        if parent and parent.type == "export_statement":
            class_obj.is_export = True

        return class_obj

    def _parse_class_body(
        self,
        body_node: tree_sitter.Node,
        source_code: bytes,
        class_obj: TSClass,
    ) -> None:
        """Parse class body members."""
        for child in body_node.children:
            if child.type == "method_definition":
                method = self._parse_method(child, source_code)
                if method:
                    if method.name == "constructor":
                        class_obj.constructor = method
                    else:
                        class_obj.methods.append(method)

            elif child.type == "field_definition":
                prop = self._parse_property(child, source_code)
                if prop:
                    class_obj.properties.append(prop)

    def _parse_method(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSMethod | None:
        """Parse a method definition."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        method_name = self._get_node_text(name_node, source_code)
        method = TSMethod(method_name)

        # Get documentation comment
        method.doc_comment = self._find_doc_comment(node, source_code)

        # Parse parameters
        params_node = node.child_by_field_name("parameters")
        if params_node:
            method.parameters = self._parse_parameters(params_node, source_code)

        # Parse return type
        return_type_node = node.child_by_field_name("return_type")
        if return_type_node:
            method.return_type = self._get_node_text(
                return_type_node, source_code
            )

        return method

    def _parse_property(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSProperty | None:
        """Parse a property definition."""
        name_node = node.child_by_field_name("property")
        if not name_node:
            return None

        prop_name = self._get_node_text(name_node, source_code)
        prop = TSProperty(prop_name)

        # Get documentation comment
        prop.doc_comment = self._find_doc_comment(node, source_code)

        # Parse type annotation
        type_node = node.child_by_field_name("type")
        if type_node:
            prop.type_annotation = self._get_node_text(type_node, source_code)

        # Parse default value
        value_node = node.child_by_field_name("value")
        if value_node:
            prop.default_value = self._get_node_text(value_node, source_code)

        return prop

    def _parse_interface(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSInterface | None:
        """Parse an interface declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        interface_name = self._get_node_text(name_node, source_code)
        interface_obj = TSInterface(interface_name)

        # Get documentation comment
        interface_obj.doc_comment = self._find_doc_comment(node, source_code)

        # Parse interface body
        body_node = node.child_by_field_name("body")
        if body_node:
            self._parse_interface_body(body_node, source_code, interface_obj)

        # Check for export modifier
        parent = node.parent
        if parent and parent.type == "export_statement":
            interface_obj.is_export = True

        return interface_obj

    def _parse_interface_body(
        self,
        body_node: tree_sitter.Node,
        source_code: bytes,
        interface_obj: TSInterface,
    ) -> None:
        """Parse interface body members."""
        for child in body_node.children:
            if child.type == "property_signature":
                prop = self._parse_interface_property(child, source_code)
                if prop:
                    interface_obj.properties.append(prop)

            elif child.type == "method_signature":
                method = self._parse_interface_method(child, source_code)
                if method:
                    interface_obj.methods.append(method)

    def _parse_interface_property(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSProperty | None:
        """Parse an interface property signature."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        prop_name = self._get_node_text(name_node, source_code)
        prop = TSProperty(prop_name)

        # Parse type annotation
        type_node = node.child_by_field_name("type")
        if type_node:
            prop.type_annotation = self._get_node_text(type_node, source_code)

        return prop

    def _parse_interface_method(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSMethod | None:
        """Parse an interface method signature."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        method_name = self._get_node_text(name_node, source_code)
        method = TSMethod(method_name)

        # Parse parameters
        params_node = node.child_by_field_name("parameters")
        if params_node:
            method.parameters = self._parse_parameters(params_node, source_code)

        # Parse return type
        return_type_node = node.child_by_field_name("return_type")
        if return_type_node:
            method.return_type = self._get_node_text(
                return_type_node, source_code
            )

        return method

    def _parse_variable_declaration(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> list[TSVariable]:
        """Parse variable declarations."""
        variables = []

        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node:
                    var_name = self._get_node_text(name_node, source_code)
                    var_obj = TSVariable(var_name)

                    # Get documentation comment
                    var_obj.doc_comment = self._find_doc_comment(
                        node, source_code
                    )

                    # Parse type annotation
                    type_node = child.child_by_field_name("type")
                    if type_node:
                        var_obj.type_annotation = self._get_node_text(
                            type_node,
                            source_code,
                        )

                    # Parse value
                    value_node = child.child_by_field_name("value")
                    if value_node:
                        var_obj.value = self._get_node_text(
                            value_node, source_code
                        )

                    # Determine variable kind (let, const, var)
                    kind_node = node.child_by_field_name("kind")
                    if kind_node:
                        var_obj.kind = self._get_node_text(
                            kind_node, source_code
                        )

                    variables.append(var_obj)

        return variables

    def _parse_function(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSMethod | None:
        """Parse a function declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        func_name = self._get_node_text(name_node, source_code)
        func = TSMethod(func_name)
        func.kind = "function"

        # Get documentation comment
        func.doc_comment = self._find_doc_comment(node, source_code)

        # Parse parameters
        params_node = node.child_by_field_name("parameters")
        if params_node:
            func.parameters = self._parse_parameters(params_node, source_code)

        # Parse return type
        return_type_node = node.child_by_field_name("return_type")
        if return_type_node:
            func.return_type = self._get_node_text(
                return_type_node, source_code
            )

        return func

    def _parse_parameters(
        self,
        params_node: tree_sitter.Node,
        source_code: bytes,
    ) -> list[dict[str, Any]]:
        """Parse function/method parameters."""
        parameters = []

        for child in params_node.children:
            if child.type in ["required_parameter", "optional_parameter"]:
                param_info = {}

                # Get parameter name
                pattern_node = child.child_by_field_name("pattern")
                if pattern_node:
                    param_info["name"] = self._get_node_text(
                        pattern_node, source_code
                    )

                # Get parameter type
                type_node = child.child_by_field_name("type")
                if type_node:
                    param_info["type"] = self._get_node_text(
                        type_node, source_code
                    )

                # Check if optional
                param_info["optional"] = child.type == "optional_parameter"

                # Get default value if present
                value_node = child.child_by_field_name("value")
                if value_node:
                    param_info["default"] = self._get_node_text(
                        value_node, source_code
                    )

                parameters.append(param_info)

        return parameters
