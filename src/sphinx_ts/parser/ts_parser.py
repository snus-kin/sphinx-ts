"""TypeScript Parser Module.

Contains the main TSParser class that uses Tree-sitter to parse TypeScript
files and extract information about classes, interfaces, variables, functions,
and enums.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import tree_sitter
from tree_sitter import Language, Parser
from tree_sitter_typescript import language_typescript

from .ast_nodes import (
    TSClass,
    TSEnum,
    TSEnumMember,
    TSInterface,
    TSMethod,
    TSProperty,
    TSVariable,
)
from .doc_comment import TSDocComment

logger = logging.getLogger(__name__)


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
                "enums": [],
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
            "enums": [],
            "types": [],
            "file_path": file_path,
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

        elif node.type == "type_alias_declaration":
            type_alias_obj = self._parse_type_alias(node, source_code)
            if type_alias_obj:
                result["types"].append(type_alias_obj)

        elif node.type == "enum_declaration":
            enum_obj = self._parse_enum(node, source_code)
            if enum_obj:
                result["enums"].append(enum_obj)

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
                elif child.type == "enum_declaration":
                    enum_obj = self._parse_enum(child, source_code)
                    if enum_obj:
                        result["enums"].append(enum_obj)
                elif child.type == "type_alias_declaration":
                    type_alias_obj = self._parse_type_alias(child, source_code)
                    if type_alias_obj:
                        result["types"].append(type_alias_obj)

        # Recursively traverse child nodes
        # Skip children if this is an export statement that we've already
        # processed
        if node.type != "export_statement" or not any(
            child.type
            in [
                "variable_declaration",
                "lexical_declaration",
                "enum_declaration",
            ]
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
        # For exported classes, the comment might be a sibling of export
        if node.parent and node.parent.type == "export_statement":
            # Look for comments that are siblings of the export statement
            export_node = node.parent
            current = export_node.prev_sibling
            while current:
                if current.type == "comment":
                    text = self._get_node_text(current, source_code)
                    if text.strip().startswith("/**"):
                        return TSDocComment(text)
                elif current.type not in ["comment", "export_statement"]:
                    break
                current = current.prev_sibling

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

            elif child.type in ["field_definition", "public_field_definition"]:
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
        name_node = node.child_by_field_name("name")
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

    def _parse_enum(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> TSEnum | None:
        """Parse an enum declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        enum_name = self._get_node_text(name_node, source_code)
        enum_obj = TSEnum(enum_name)

        # Get documentation comment
        enum_obj.doc_comment = self._find_doc_comment(node, source_code)

        # If no comment found and we're in an export statement, check the
        # export statement
        if (
            not enum_obj.doc_comment
            and node.parent
            and node.parent.type == "export_statement"
        ):
            enum_obj.doc_comment = self._find_doc_comment(
                node.parent, source_code
            )

        # Check for const enum
        for child in node.children:
            if child.type == "const" or (
                hasattr(child, "text") and child.text == b"const"
            ):
                enum_obj.is_const = True
                break

        # Check for declare enum
        parent = node.parent
        if parent and parent.type == "ambient_declaration":
            enum_obj.is_declare = True

        # Check for export modifier
        if parent and parent.type == "export_statement":
            enum_obj.is_export = True

        # Parse enum body
        body_node = node.child_by_field_name("body")
        if body_node:
            self._parse_enum_body(body_node, source_code, enum_obj)

        return enum_obj

    def _parse_enum_body(
        self,
        body_node: tree_sitter.Node,
        source_code: bytes,
        enum_obj: TSEnum,
    ) -> None:
        """Parse enum body members."""
        for child in body_node.children:
            if child.type == "property_identifier":
                # Simple enum member without value
                member_name = self._get_node_text(child, source_code)
                member = TSEnumMember(member_name)
                member.doc_comment = self._find_doc_comment(child, source_code)
                enum_obj.members.append(member)
            elif child.type == "enum_assignment":
                # Enum member with assignment
                name_node = child.child_by_field_name("name")
                value_node = child.child_by_field_name("value")

                if name_node:
                    member_name = self._get_node_text(name_node, source_code)
                    member = TSEnumMember(member_name)
                    member.doc_comment = self._find_doc_comment(
                        child, source_code
                    )

                    if value_node:
                        member.value = self._get_node_text(
                            value_node, source_code
                        )
                        # Check if the value is computed (contains expressions)
                        member.computed_value = value_node.type not in [
                            "string",
                            "number",
                            "true",
                            "false",
                        ]

                    enum_obj.members.append(member)

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

        siblings = list(node.parent.children)
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
                        # Look for doc comments directly above the variable
                        # declarator
                        prev_sibling = self._get_previous_sibling(child)
                        if prev_sibling and prev_sibling.type == "comment":
                            comment_text = self._get_node_text(
                                prev_sibling, source_code
                            )
                            if comment_text.startswith("/**"):
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

    def _parse_type_alias(
        self,
        node: tree_sitter.Node,
        source_code: bytes,
    ) -> dict[str, Any] | None:
        """Parse a TypeScript type alias declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        type_alias_name = self._get_node_text(name_node, source_code)

        # Get the type definition
        type_node = node.child_by_field_name("value")
        type_definition = ""
        if type_node:
            type_definition = self._get_node_text(type_node, source_code)

        # Get type parameters if present
        type_parameters_node = node.child_by_field_name("type_parameters")
        type_parameters = []
        if type_parameters_node:
            for child in type_parameters_node.children:
                if child.type == "type_identifier":
                    type_parameters.append(
                        self._get_node_text(child, source_code)
                    )

        # Find associated documentation comment
        doc_comment = self._find_doc_comment(node, source_code)

        return {
            "name": type_alias_name,
            "type_definition": type_definition,
            "type_parameters": type_parameters,
            "doc_comment": doc_comment,
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
        }
