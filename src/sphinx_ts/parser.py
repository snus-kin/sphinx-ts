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

        # Clear examples list before parsing to avoid duplicates
        self.examples = []

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
                # Process markdown code blocks more carefully
                tag_value = re.sub(r"```typescript\s*", "", tag_value)
                tag_value = re.sub(r"```\s*$", "", tag_value)
                tag_value = tag_value.strip()
                if tag_value:  # Only add non-empty examples
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
        self.is_export = False

    def __lt__(self, other: Any) -> bool:
        """Support sorting of TSMember objects by name."""
        if isinstance(other, TSMember):
            return self.name.lower() < other.name.lower()
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Support equality comparison of TSMember objects."""
        if isinstance(other, TSMember):
            return self.name.lower() == other.name.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Support using TSMember objects as dictionary keys."""
        return hash(self.name.lower())


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

    def __lt__(self, other: Any) -> bool:
        """Support sorting of TSMethod objects by name."""
        if isinstance(other, TSMethod):
            return self.name.lower() < other.name.lower()
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Support equality comparison of TSMethod objects."""
        if isinstance(other, TSMethod):
            return self.name.lower() == other.name.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Support using TSMethod objects as dictionary keys."""
        return hash(self.name.lower())


class TSProperty(TSMember):
    """Represents a TypeScript property."""

    def __init__(self, name: str) -> None:
        """Initialize a TypeScript property.

        Args:
            name: The name of the property

        """
        super().__init__(name, "property")
        self.default_value: str | None = None

    def __lt__(self, other: Any) -> bool:
        """Support sorting of TSProperty objects by name."""
        if isinstance(other, TSProperty):
            return self.name.lower() < other.name.lower()
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Support equality comparison of TSProperty objects."""
        if isinstance(other, TSProperty):
            return self.name.lower() == other.name.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Support using TSProperty objects as dictionary keys."""
        return hash(self.name.lower())


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

    def __lt__(self, other: Any) -> bool:
        """Support sorting of TSClass objects by name."""
        if isinstance(other, TSClass):
            return self.name.lower() < other.name.lower()
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Support equality comparison of TSClass objects."""
        if isinstance(other, TSClass):
            return self.name.lower() == other.name.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Support using TSClass objects as dictionary keys."""
        return hash(self.name.lower())


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

    def __lt__(self, other: Any) -> bool:
        """Support sorting of TSInterface objects by name."""
        if isinstance(other, TSInterface):
            return self.name.lower() < other.name.lower()
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Support equality comparison of TSInterface objects."""
        if isinstance(other, TSInterface):
            return self.name.lower() == other.name.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Support using TSInterface objects as dictionary keys."""
        return hash(self.name.lower())


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

    def __lt__(self, other: Any) -> bool:
        """Support sorting of TSVariable objects by name."""
        if isinstance(other, TSVariable):
            return self.name.lower() < other.name.lower()
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        """Support equality comparison of TSVariable objects."""
        if isinstance(other, TSVariable):
            return self.name.lower() == other.name.lower()
        return NotImplemented

    def __hash__(self) -> int:
        """Support using TSVariable objects as dictionary keys."""
        return hash(self.name.lower())


class TSValueParser:
    """Parser for TypeScript values and literals."""

    @staticmethod
    def parse_value(value: str | None) -> dict:
        """Parse a TypeScript value into a structured representation.

        Args:
            value: The TypeScript value as a string

        Returns:
            A dictionary with information about the value

        """
        if value is None or not value.strip():
            return {"type": "unknown", "value": "", "properties": []}

        value = value.strip()

        # Create a parser for the fragment
        parser = Parser()
        language = Language(language_typescript())
        parser.language = language

        # Wrap the value in a variable declaration to help parser
        wrapper = f"const __temp__ = {value};"
        tree = parser.parse(bytes(wrapper, "utf8"))

        if not tree or not tree.root_node:
            return {"type": "unknown", "value": value, "properties": []}

        # Find the value node
        value_node = None
        for node in tree.root_node.children:
            if node.type == "lexical_declaration":
                for child in node.children:
                    if child.type == "variable_declarator":
                        value_node = child.child_by_field_name("value")
                        break
                break

        if not value_node:
            return {"type": "unknown", "value": value, "properties": []}

        # Parse based on node type
        if value_node.type == "object":
            return TSValueParser._parse_object(value_node, wrapper)
        if value_node.type == "array":
            return TSValueParser._parse_array(value_node, wrapper)
        if value_node.type in ["string", "template_string"]:
            return {"type": "string", "value": value, "properties": []}
        if value_node.type == "number":
            return {"type": "number", "value": value, "properties": []}
        if value_node.type == "true" or value_node.type == "false":
            return {"type": "boolean", "value": value, "properties": []}
        if value_node.type == "null":
            return {"type": "null", "value": "null", "properties": []}
        if value_node.type == "undefined":
            return {"type": "undefined", "value": "undefined", "properties": []}
        if value_node.type == "function":
            return {"type": "function", "value": value, "properties": []}
        return {"type": "unknown", "value": value, "properties": []}

    @staticmethod
    def _parse_object(node: tree_sitter.Node, source_code: str) -> dict:
        """Parse an object literal."""
        properties = []
        object_type = "object"

        for child in node.children:
            if child.type == "pair":
                key_node = child.child_by_field_name("key")
                value_node = child.child_by_field_name("value")

                if key_node and value_node:
                    key = source_code[key_node.start_byte : key_node.end_byte]
                    value = source_code[
                        value_node.start_byte : value_node.end_byte
                    ]

                    # Clean up the key if it's a string
                    if key.startswith('"') or key.startswith("'"):
                        key = key[1:-1]

                    # Parse the property value recursively
                    prop_value = None
                    prop_type = "unknown"

                    if value_node.type == "object":
                        prop_value = "{...}"
                        prop_type = "object"
                    elif value_node.type == "array":
                        prop_value = "[...]"
                        prop_type = "array"
                    elif value_node.type in ["string", "template_string"]:
                        prop_value = value
                        prop_type = "string"
                    elif value_node.type == "number":
                        prop_value = value
                        prop_type = "number"
                    elif (
                        value_node.type == "true" or value_node.type == "false"
                    ):
                        prop_value = value
                        prop_type = "boolean"
                    elif value_node.type == "null":
                        prop_value = "null"
                        prop_type = "null"
                    elif value_node.type == "undefined":
                        prop_value = "undefined"
                        prop_type = "undefined"
                    else:
                        prop_value = value

                    properties.append(
                        {"key": key, "value": prop_value, "type": prop_type}
                    )

        return {"type": object_type, "value": "{...}", "properties": properties}

    @staticmethod
    def _parse_array(node: tree_sitter.Node, source_code: str) -> dict:
        """Parse an array literal."""
        items = []
        array_type = "array"
        element_type = "unknown"

        # Try to determine element type
        element_types = set()

        for child in node.children:
            if child.type not in [",", "[", "]"]:
                value = source_code[child.start_byte : child.end_byte]

                item_type = "unknown"
                if child.type == "object":
                    item_type = "object"
                elif child.type == "array":
                    item_type = "array"
                elif child.type in ["string", "template_string"]:
                    item_type = "string"
                elif child.type == "number":
                    item_type = "number"
                elif child.type == "true" or child.type == "false":
                    item_type = "boolean"

                element_types.add(item_type)

                items.append({"value": value, "type": item_type})

        # Determine the array element type
        if len(element_types) == 1:
            element_type = next(iter(element_types))
            array_type = f"{element_type}[]"

        return {
            "type": array_type,
            "value": "[...]",
            "items": items,
            "element_type": element_type,
            "properties": [],
        }

    @staticmethod
    def format_value(value: str | None, pretty: bool = True) -> str:
        """Format a TypeScript value for display.

        Args:
            value: The TypeScript value as a string
            pretty: Whether to pretty-print the value

        Returns:
            A formatted string representation of the value

        """
        if value is None or not value.strip():
            return ""

        value = value.strip()

        # Parse the value
        parsed = TSValueParser.parse_value(value)

        # Always pretty-print objects and arrays, regardless of their complexity
        # This ensures constants like MATH_CONSTANTS are properly formatted
        if not pretty or (
            parsed["type"] != "object"
            and not parsed["type"].endswith("[]")
            and not (value.startswith("{") and value.endswith("}"))
            and not (value.startswith("[") and value.endswith("]"))
        ):
            return value

        # Create a parser for proper formatting
        parser = Parser()
        language = Language(language_typescript())
        parser.language = language

        # Wrap in a declaration for easier parsing
        wrapper = f"const __temp__ = {value};"
        tree = parser.parse(bytes(wrapper, "utf8"))

        if not tree or not tree.root_node:
            return value

        try:
            # Find the declaration node
            for node in tree.root_node.children:
                if node.type == "lexical_declaration":
                    # Format the code with proper indentation
                    value_node = None
                    for child in node.children:
                        if child.type == "variable_declarator":
                            value_node = child.child_by_field_name("value")
                            break

                    if value_node:
                        formatted = TSValueParser._format_node(
                            value_node, bytes(wrapper, "utf8"), 0
                        )
                        return formatted
        except Exception:
            # If formatting fails, return the original
            return value

        return value

    @staticmethod
    def _format_node(
        node: tree_sitter.Node, source_code: bytes, indent_level: int = 0
    ) -> str:
        """Format a node with proper indentation.

        Args:
            node: The Tree-sitter node
            source_code: The source code
            indent_level: Current indentation level

        Returns:
            Formatted code string

        """
        node_type = node.type

        # Handle comments attached to the node (if available)
        comments = []
        prev_sibling = node.prev_sibling
        if prev_sibling and prev_sibling.type == "comment":
            comments.append(
                source_code[
                    prev_sibling.start_byte : prev_sibling.end_byte
                ].decode("utf-8")
            )

        # Simple literals
        if node_type in [
            "string",
            "template_string",
            "number",
            "true",
            "false",
            "null",
            "undefined",
        ]:
            literal = source_code[node.start_byte : node.end_byte].decode(
                "utf-8"
            )
            if comments:
                return f"{' '.join(comments)} {literal}"
            return literal

        # Arrays
        if node_type == "array":
            items = []
            for child in node.children:
                if child.type not in [",", "[", "]"]:
                    items.append(
                        TSValueParser._format_node(
                            child, source_code, indent_level + 1
                        )
                    )

            # Format based on complexity - for const objects, always use multi-line format
            if len(items) == 0:
                return "[]"
            # For small arrays with simple items, use single-line format
            if (
                indent_level > 0
                and len(items) <= 3
                and all(len(item) < 30 for item in items)
            ):
                result = f"[{', '.join(items)}]"
                if comments:
                    return f"{' '.join(comments)} {result}"
                return result

            # For larger arrays or top-level arrays (likely constants), use multi-line format
            indent = "  " * indent_level
            inner_indent = "  " * (indent_level + 1)
            result = (
                f"[\n{inner_indent}"
                + f",\n{inner_indent}".join(items)
                + f"\n{indent}]"
            )
            if comments and indent_level == 0:
                # Only add comments at the top level to avoid messing up nested formatting
                result = f"{' '.join(comments)}\n{result}"
            return result

        # Objects
        if node_type == "object":
            pairs = []
            for child in node.children:
                if child.type == "pair":
                    key_node = child.child_by_field_name("key")
                    value_node = child.child_by_field_name("value")

                    if key_node and value_node:
                        key = source_code[
                            key_node.start_byte : key_node.end_byte
                        ].decode("utf-8")
                        value = TSValueParser._format_node(
                            value_node, source_code, indent_level + 1
                        )
                        pairs.append(f"{key}: {value}")

            # Format based on complexity
            if len(pairs) == 0:
                return "{}"

            # For small objects with simple properties at nested levels, use single-line format
            if (
                indent_level > 0
                and len(pairs) <= 2
                and all(len(pair) < 40 for pair in pairs)
            ):
                result = f"{{ {', '.join(pairs)} }}"
                if comments:
                    return f"{' '.join(comments)} {result}"
                return result

            # For larger objects or top-level objects (likely constants), use multi-line format
            indent = "  " * indent_level
            inner_indent = "  " * (indent_level + 1)
            result = (
                f"{{\n{inner_indent}"
                + f",\n{inner_indent}".join(pairs)
                + f"\n{indent}}}"
            )
            if comments and indent_level == 0:
                # Only add comments at the top level to avoid messing up nested formatting
                result = f"{' '.join(comments)}\n{result}"
            return result

        # Default
        default_result = source_code[node.start_byte : node.end_byte].decode(
            "utf-8"
        )
        if comments:
            return f"{' '.join(comments)} {default_result}"
        return default_result


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

        elif node.type == "lexical_declaration":
            # Only process if not inside an export statement
            if node.parent and node.parent.type != "export_statement":
                variables = self._parse_variable_declaration(node, source_code)
                result["variables"].extend(variables)

        elif node.type == "function_declaration":
            function_obj = self._parse_function(node, source_code)
            if function_obj:
                result["functions"].append(function_obj)

        elif node.type == "export_statement":
            for child in node.children:
                if child.type in [
                    "variable_declaration",
                    "lexical_declaration",
                ]:
                    variables = self._parse_variable_declaration(
                        child, source_code
                    )
                    result["variables"].extend(variables)
                elif child.type == "function_declaration":
                    function_obj = self._parse_function(child, source_code)
                    if function_obj:
                        result["functions"].append(function_obj)

        # Recursively traverse child nodes
        # Skip children if this is an export statement that we've already processed
        if node.type != "export_statement" or not any(
            child.type in ["variable_declaration", "lexical_declaration"]
            for child in node.children
        ):
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

    def _get_previous_sibling(
        self, node: tree_sitter.Node
    ) -> tree_sitter.Node | None:
        """Get the previous sibling of a node."""
        if not node.parent:
            return None

        siblings = [child for child in node.parent.children]
        for i, sibling in enumerate(siblings):
            if sibling.id == node.id and i > 0:
                return siblings[i - 1]
        return None

    def _parse_variable_declaration(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> list[TSVariable]:
        """Parse variable declarations."""
        variables = []

        # Check if this is an export declaration
        is_export = False
        parent = node.parent
        if parent and parent.type == "export_statement":
            is_export = True

        # Store seen variable names to avoid duplicates
        seen_variables = set()

        for child in node.children:
            if child.type == "variable_declarator":
                name_node = child.child_by_field_name("name")
                if name_node:
                    var_name = self._get_node_text(name_node, source_code)
                    var_obj = TSVariable(var_name)
                    var_obj.is_export = is_export

                    # Try to find doc comment for the variable
                    # First check node (declaration level)
                    var_obj.doc_comment = self._find_doc_comment(
                        node, source_code
                    )

                    # If not found, check parent for export statements
                    if (
                        not var_obj.doc_comment
                        and parent
                        and parent.type == "export_statement"
                    ):
                        var_obj.doc_comment = self._find_doc_comment(
                            parent, source_code
                        )

                    # Also look at export statements with multiple variables
                    if not var_obj.doc_comment:
                        # Look for doc comments directly above the variable declarator
                        prev_sibling = self._get_previous_sibling(child)
                        if prev_sibling and prev_sibling.type == "comment":
                            comment_text = self._get_node_text(
                                prev_sibling, source_code
                            )
                            if comment_text.startswith("/**"):
                                from sphinx_ts.parser import TSDocComment

                                var_obj.doc_comment = TSDocComment(comment_text)

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

                    # Only add the variable if we haven't seen it before
                    if var_name not in seen_variables:
                        seen_variables.add(var_name)
                        variables.append(var_obj)
                    else:
                        continue

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

        # Check for export modifier
        parent = node.parent
        if parent and parent.type == "export_statement":
            func.is_export = True

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
