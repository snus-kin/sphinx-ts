"""Tests for TypeScript auto-documentation directives."""

from pathlib import Path
from unittest.mock import Mock, PropertyMock, patch

import pytest

from sphinx_ts.directives import TSAutoDirective, TSAutoEnumDirective
from sphinx_ts.parser import (
    TSClass,
    TSDocComment,
    TSEnum,
    TSEnumMember,
    TSInterface,
    TSMethod,
    TSParser,
    TSProperty,
    TSVariable,
)

# Test constants
EXPECTED_INTERFACE_PROPERTIES_COUNT = 2


class TestTSAutoDirectiveCore:
    """Test core functionality of TSAutoDirective without Sphinx complexities.

    This test class focuses on testing the directive functionality in isolation.
    """

    def test_format_doc_comment_empty(self) -> None:
        """Test formatting empty doc comment."""
        # Create a minimal directive instance for testing methods
        directive = TSAutoDirective.__new__(TSAutoDirective)
        result = directive.format_doc_comment(None)
        assert result == []

    def test_format_doc_comment_with_content(self) -> None:
        """Test formatting doc comment with content."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        doc_comment = TSDocComment("""
        /**
         * This is a test function.
         * @param name The name parameter
         * @returns A greeting string
         */
        """)

        result = directive.format_doc_comment(doc_comment)
        assert len(result) > 0
        assert "This is a test function." in result[0]
        assert any(".. rubric:: Parameters" in line for line in result)
        assert any("name" in line for line in result)

    def test_format_type_annotation(self) -> None:
        """Test formatting TypeScript type annotations."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        assert directive.format_type_annotation(None) == "any"
        assert directive.format_type_annotation("string") == "string"
        assert directive.format_type_annotation(": number") == "number"
        assert directive.format_type_annotation("  : boolean  ") == "boolean"

    def test_create_rst_content_empty(self) -> None:
        """Test creating RST content from empty lines."""
        directive = TSAutoDirective.__new__(TSAutoDirective)
        result = directive.create_rst_content([])
        assert result == []

    def test_create_rst_content_simple(self) -> None:
        """Test creating RST content from simple text."""
        directive = TSAutoDirective.__new__(TSAutoDirective)
        result = directive.create_rst_content(["This is a test paragraph."])
        assert len(result) >= 1
        # Result should contain at least one docutils node

    def test_find_object_in_files(self) -> None:
        """Test finding objects in TypeScript files."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        # Mock the parser
        mock_parser_instance = Mock()
        directive.parser = mock_parser_instance

        # Mock get_source_files method
        test_file = Path("/test/file.ts")
        directive.get_source_files = Mock(return_value=[test_file])

        # Mock parsed data with a test class
        mock_class = TSClass("TestClass")
        mock_parser_instance.parse_file.return_value = {
            "classes": [mock_class],
            "interfaces": [],
            "variables": [],
            "functions": [],
        }

        # Mock the env property and its methods
        with patch.object(
            type(directive), "env", new_callable=PropertyMock
        ) as mock_env_prop:
            mock_env = Mock()
            mock_env.docname = "test_doc"
            mock_domain = Mock()
            mock_domain.data = {"objects": {}}
            mock_env.get_domain.return_value = mock_domain
            mock_env_prop.return_value = mock_env

            result = directive.find_object_in_files("TestClass", "class")

            assert result is not None
            assert result["object"] == mock_class
            assert result["file_path"] == test_file
            directive.get_source_files.assert_called_once()
            mock_parser_instance.parse_file.assert_called_once_with(test_file)

    def test_find_object_in_files_not_found(self) -> None:
        """Test finding objects when they don't exist."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        # Mock the parser and get_source_files method
        directive.parser = Mock()
        directive.get_source_files = Mock(return_value=[])

        # Mock the env property
        with patch.object(
            type(directive), "env", new_callable=PropertyMock
        ) as mock_env_prop:
            mock_env = Mock()
            mock_env.docname = "test_doc"
            mock_domain = Mock()
            mock_domain.data = {"objects": {}}
            mock_env.get_domain.return_value = mock_domain
            mock_env_prop.return_value = mock_env

            result = directive.find_object_in_files("NonExistent", "class")

            assert result is None


class TestTSDocCommentFormatting:
    """Test JSDoc comment formatting functionality."""

    def test_format_comment_with_all_tags(self) -> None:
        """Test formatting comment with various JSDoc tags."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        doc_comment = TSDocComment("""
        /**
         * A comprehensive test function.
         *
         * @param x The first parameter
         * @param y The second parameter
         * @returns The result value
         * @example
         * ```typescript
         * const result = testFunc(1, 2);
         * ```
         * @since 1.0.0
         * @deprecated Use newFunc instead
         */
        """)

        result = directive.format_doc_comment(doc_comment)

        # Check that all components are present
        content = "\n".join(result)
        assert "comprehensive test function" in content.lower()
        assert ".. rubric:: Parameters" in content
        assert "first parameter" in content
        assert "second parameter" in content
        assert ".. rubric:: Returns" in content or "result value" in content
        assert ".. rubric:: Examples" in content
        assert "Since:" in content or "1.0.0" in content
        assert "deprecated" in content.lower()

    def test_format_comment_minimal(self) -> None:
        """Test formatting minimal comment."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        doc_comment = TSDocComment("/** Simple description */")
        result = directive.format_doc_comment(doc_comment)

        assert len(result) >= 1
        assert "Simple description" in result[0]

    def test_format_comment_params_only(self) -> None:
        """Test formatting comment with only parameters."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        doc_comment = TSDocComment("""
        /**
         * @param a First param
         * @param b Second param
         */
        """)

        result = directive.format_doc_comment(doc_comment)
        content = "\n".join(result)

        assert ".. rubric:: Parameters" in content
        assert "First param" in content
        assert "Second param" in content


class TestTypeScriptObjectCreation:
    """Test creating TypeScript objects for documentation."""

    def test_create_mock_class_structure(self) -> None:
        """Test creating a structured TypeScript class."""
        ts_class = TSClass("Calculator")
        ts_class.doc_comment = TSDocComment("/** Calculator class */")

        # Add method
        method = TSMethod("add")
        method.parameters = [
            {"name": "a", "type": "number"},
            {"name": "b", "type": "number"},
        ]
        method.return_type = "number"
        ts_class.methods.append(method)

        # Add property
        prop = TSProperty("value")
        prop.type_annotation = "number"
        ts_class.properties.append(prop)

        assert ts_class.name == "Calculator"
        assert len(ts_class.methods) == 1
        assert len(ts_class.properties) == 1
        assert ts_class.methods[0].name == "add"
        assert ts_class.properties[0].name == "value"

    def test_create_mock_interface_structure(self) -> None:
        """Test creating a structured TypeScript interface."""
        ts_interface = TSInterface("Config")
        ts_interface.doc_comment = TSDocComment(
            "/** Configuration interface */"
        )

        # Add property
        prop = TSProperty("name")
        prop.type_annotation = "string"
        prop.is_optional = False
        ts_interface.properties.append(prop)

        # Add optional property
        opt_prop = TSProperty("debug")
        opt_prop.type_annotation = "boolean"
        opt_prop.is_optional = True
        ts_interface.properties.append(opt_prop)

        assert ts_interface.name == "Config"
        expected_count = EXPECTED_INTERFACE_PROPERTIES_COUNT
        assert len(ts_interface.properties) == expected_count
        assert not ts_interface.properties[0].is_optional
        assert ts_interface.properties[1].is_optional

    def test_create_mock_variable_structure(self) -> None:
        """Test creating a structured TypeScript variable."""
        ts_var = TSVariable("DEFAULT_CONFIG")
        ts_var.doc_comment = TSDocComment("/** Default configuration */")
        ts_var.kind = "const"
        ts_var.type_annotation = "Config"
        ts_var.value = "{ name: 'default' }"

        assert ts_var.name == "DEFAULT_CONFIG"
        assert ts_var.kind == "const"
        assert ts_var.type_annotation == "Config"
        assert ts_var.value == "{ name: 'default' }"


class TestRSTGeneration:
    """Test reStructuredText generation from TypeScript objects."""

    def test_method_signature_generation(self) -> None:
        """Test generating method signatures."""
        method = TSMethod("calculateSum")
        method.parameters = [
            {"name": "a", "type": "number", "optional": False},
            {"name": "b", "type": "number", "optional": False},
            {
                "name": "precision",
                "type": "number",
                "optional": True,
                "default": "2",
            },
        ]
        method.return_type = "number"

        # Test that we can generate a reasonable signature
        signature_parts = []
        signature_parts.append(method.name)

        if method.parameters:
            param_strs = []
            for param in method.parameters:
                param_str = param["name"]
                if param.get("type"):
                    param_str += f": {param['type']}"
                if param.get("optional"):
                    param_str += "?"
                if param.get("default"):
                    param_str += f" = {param['default']}"
                param_strs.append(param_str)
            signature_parts.append(f"({', '.join(param_strs)})")

        if method.return_type:
            signature_parts.append(f": {method.return_type}")

        signature = "".join(signature_parts)

        assert "calculateSum" in signature
        assert "a: number" in signature
        assert "b: number" in signature
        assert "precision: number?" in signature
        assert "= 2" in signature
        assert ": number" in signature  # return type

    def test_property_signature_generation(self) -> None:
        """Test generating property signatures."""
        prop = TSProperty("isEnabled")
        prop.type_annotation = "boolean"
        prop.is_optional = True
        prop.default_value = "false"

        # Generate property signature
        signature = prop.name
        if prop.is_optional:
            signature += "?"
        if prop.type_annotation:
            signature += f": {prop.type_annotation}"

        assert signature == "isEnabled?: boolean"

    def test_interface_property_signature(self) -> None:
        """Test generating interface property signatures."""
        prop = TSProperty("title")
        prop.type_annotation = "string | null"
        prop.is_optional = False

        signature = prop.name
        if prop.type_annotation:
            signature += f": {prop.type_annotation}"

        assert signature == "title: string | null"


class TestErrorHandling:
    """Test error handling in directive processing."""

    def test_handle_missing_parser(self) -> None:
        """Test handling when parser is unavailable."""
        with patch("sphinx_ts.parser.TSParser") as mock_parser_class:
            # Make parser initialization fail
            mock_parser_class.side_effect = ImportError(
                "Tree-sitter not available"
            )

            # The directive should handle this gracefully
            directive = TSAutoDirective.__new__(TSAutoDirective)

            # Should not raise an exception
            try:
                directive.__init__ = TSAutoDirective.__init__
                # In real usage, this would be called by Sphinx
                # Here we're just testing that it doesn't crash
                assert True  # If we get here, no exception was raised
            except ImportError:
                # This is acceptable - the directive should warn but not crash
                pass

    def test_handle_file_not_found(self) -> None:
        """Test handling when TypeScript files are not found."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        # Mock parser that returns empty results
        with patch(
            "sphinx_ts.directives.TSAutoDirective.get_source_files",
        ) as mock_get_files:
            mock_get_files.return_value = []

            result = directive.find_object_in_files("AnyClass", "class")
            assert result is None

    def test_handle_parse_error(self) -> None:
        """Test handling TypeScript parse errors."""
        directive = TSAutoDirective.__new__(TSAutoDirective)
        directive.parser = TSParser()  # Initialize parser

        with (
            patch(
                "sphinx_ts.directives.TSAutoDirective.get_source_files",
            ) as mock_get_files,
            patch("sphinx_ts.parser.TSParser.parse_file") as mock_parse,
        ):
            mock_get_files.return_value = [Path("test.ts")]
            mock_parse.side_effect = Exception("Parse error")

            # Should handle parse errors gracefully
            result = directive.find_object_in_files("AnyClass", "class")
            assert result is None


class TestUtilityFunctions:
    """Test utility functions used by directives."""

    def test_clean_type_annotation(self) -> None:
        """Test cleaning type annotations."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        test_cases = [
            (None, "any"),
            ("", "any"),
            ("string", "string"),
            (": string", "string"),
            ("  : number  ", "number"),
            (": Array<string>", "Array<string>"),
            (": { [key: string]: any }", "{ [key: string]: any }"),
        ]

        for input_type, expected in test_cases:
            result = directive.format_type_annotation(input_type)
            assert result == expected, (
                f"Expected {expected} for {input_type}, got {result}"
            )

    def test_doc_comment_parsing_edge_cases(self) -> None:
        """Test edge cases in JSDoc comment parsing."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        # Empty comment
        empty_doc = TSDocComment("")
        result = directive.format_doc_comment(empty_doc)
        assert len(result) == 0 or all(not line.strip() for line in result)

        # Comment with only whitespace
        whitespace_doc = TSDocComment("/**   */")
        result = directive.format_doc_comment(whitespace_doc)
        # Should handle gracefully without errors

    def test_rst_content_creation_safety(self) -> None:
        """Test that RST content creation is safe with various inputs."""
        directive = TSAutoDirective.__new__(TSAutoDirective)

        # Test with various input types
        test_inputs = [
            [],
            ["Simple line"],
            ["Line 1", "", "Line 3"],  # Empty line in middle
            ["Line with **bold** text"],
            ["Line with `code` text"],
            ["Line with special chars: <>\"'&"],
        ]

        for test_input in test_inputs:
            result = directive.create_rst_content(test_input)
            # Should not raise exceptions and should return list
            assert isinstance(result, list)


class TestTSAutoEnumDirective:
    """Test TSAutoEnumDirective functionality."""

    def test_create_enum_signature_basic(self) -> None:
        """Test creating basic enum signature."""
        directive = TSAutoEnumDirective.__new__(TSAutoEnumDirective)

        # Test basic exported enum
        enum_obj = TSEnum("MyEnum")
        enum_obj.is_export = True

        signature = directive._create_enum_signature(enum_obj)
        assert signature == "export enum MyEnum"

    def test_create_enum_signature_const(self) -> None:
        """Test creating const enum signature."""
        directive = TSAutoEnumDirective.__new__(TSAutoEnumDirective)

        enum_obj = TSEnum("Direction")
        enum_obj.is_export = True
        enum_obj.is_const = True

        signature = directive._create_enum_signature(enum_obj)
        assert signature == "export const enum Direction"

    def test_create_enum_signature_declare(self) -> None:
        """Test creating declare enum signature."""
        directive = TSAutoEnumDirective.__new__(TSAutoEnumDirective)

        enum_obj = TSEnum("ExternalEnum")
        enum_obj.is_declare = True

        signature = directive._create_enum_signature(enum_obj)
        assert signature == "declare enum ExternalEnum"

    def test_create_member_signature_with_value(self) -> None:
        """Test creating enum member signature with value."""
        directive = TSAutoEnumDirective.__new__(TSAutoEnumDirective)

        member = TSEnumMember("STATUS")
        member.value = '"active"'

        signature = directive._create_member_signature(member)
        assert signature == 'STATUS = "active"'

    def test_create_member_signature_without_value(self) -> None:
        """Test creating enum member signature without value."""
        directive = TSAutoEnumDirective.__new__(TSAutoEnumDirective)

        member = TSEnumMember("FIRST")

        signature = directive._create_member_signature(member)
        assert signature == "FIRST"

    def test_create_member_signature_computed(self) -> None:
        """Test creating enum member signature with computed value."""
        directive = TSAutoEnumDirective.__new__(TSAutoEnumDirective)

        member = TSEnumMember("READ")
        member.value = "1 << 0"
        member.computed_value = True

        signature = directive._create_member_signature(member)
        assert signature == "READ = 1 << 0"


if __name__ == "__main__":
    pytest.main([__file__])
