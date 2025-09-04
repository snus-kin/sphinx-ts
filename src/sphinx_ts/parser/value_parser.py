"""TypeScript Value Parser Module.

Contains the TSValueParser class for parsing and formatting TypeScript
values and literals.
"""

from __future__ import annotations

import tree_sitter
from tree_sitter import Language, Parser
from tree_sitter_typescript import language_typescript

# Constants for formatting limits
MAX_INLINE_ARRAY_ITEMS = 3
MAX_INLINE_ITEM_LENGTH = 30
MAX_INLINE_OBJECT_PAIRS = 2
MAX_INLINE_PAIR_LENGTH = 40


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
        if value_node.type in {"true", "false"}:
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
                    if key.startswith(('"', "'")):
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
                    elif value_node.type in {"true", "false"}:
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
                elif child.type in {"true", "false"}:
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
    def format_value(value: str | None, *, pretty: bool = True) -> str:
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
                        return TSValueParser._format_node(
                            value_node, bytes(wrapper, "utf8"), 0
                        )
        except (ValueError, TypeError, AttributeError):
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
            items = [
                TSValueParser._format_node(child, source_code, indent_level + 1)
                for child in node.children
                if child.type not in [",", "[", "]"]
            ]

            # Format based on complexity - for const objects, always use
            # multi-line format
            if len(items) == 0:
                return "[]"
            # For small arrays with simple items, use single-line format
            if (
                indent_level > 0
                and len(items) <= MAX_INLINE_ARRAY_ITEMS
                and all(len(item) < MAX_INLINE_ITEM_LENGTH for item in items)
            ):
                result = f"[{', '.join(items)}]"
                if comments:
                    return f"{' '.join(comments)} {result}"
                return result

            # For larger arrays or top-level arrays (likely constants), use
            # multi-line format
            indent = "  " * indent_level
            inner_indent = "  " * (indent_level + 1)
            result = (
                f"[\n{inner_indent}"
                + f",\n{inner_indent}".join(items)
                + f"\n{indent}]"
            )
            if comments and indent_level == 0:
                # Only add comments at the top level to avoid messing up
                # nested formatting
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

            # For small objects with simple properties at nested levels, use
            # single-line format
            if (
                indent_level > 0
                and len(pairs) <= MAX_INLINE_OBJECT_PAIRS
                and all(len(pair) < MAX_INLINE_PAIR_LENGTH for pair in pairs)
            ):
                result = f"{{ {', '.join(pairs)} }}"
                if comments:
                    return f"{' '.join(comments)} {result}"
                return result

            # For larger objects or top-level objects (likely constants), use
            # multi-line format
            indent = "  " * indent_level
            inner_indent = "  " * (indent_level + 1)
            result = (
                f"{{\n{inner_indent}"
                + f",\n{inner_indent}".join(pairs)
                + f"\n{indent}}}"
            )
            if comments and indent_level == 0:
                # Only add comments at the top level to avoid messing up
                # nested formatting
                result = f"{' '.join(comments)}\n{result}"
            return result

        # Default
        default_result = source_code[node.start_byte : node.end_byte].decode(
            "utf-8"
        )
        if comments:
            return f"{' '.join(comments)} {default_result}"
        return default_result
