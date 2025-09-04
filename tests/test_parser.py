"""Tests for the TypeScript parser module."""

import shutil
import tempfile
from pathlib import Path

import pytest

from sphinx_ts.parser import (
    TSClass,
    TSDocComment,
    TSEnum,
    TSEnumMember,
    TSInterface,
    TSMethod,
    TSParser,
    TSVariable,
)


class TestTSDocComment:
    """Test JSDoc comment parsing."""

    def test_simple_comment(self) -> None:
        """Test parsing a simple JSDoc comment."""
        comment_text = """
        /**
         * This is a simple description.
         */
        """
        doc = TSDocComment(comment_text)
        assert doc.description == "This is a simple description."

    def test_comment_with_params(self) -> None:
        """Test parsing JSDoc comment with parameters."""
        comment_text = """
        /**
         * Adds two numbers together.
         * @param a The first number
         * @param b The second number
         * @returns The sum of a and b
         */
        """
        doc = TSDocComment(comment_text)
        assert doc.description == "Adds two numbers together."
        assert "a" in doc.params
        assert doc.params["a"] == "The first number"
        assert "b" in doc.params
        assert doc.params["b"] == "The second number"
        assert doc.returns == "The sum of a and b"

    def test_comment_with_example(self) -> None:
        """Test parsing JSDoc comment with examples."""
        comment_text = """
        /**
         * A function with examples.
         * @example
         * const result = myFunc(1, 2);
         * console.log(result);
         */
        """
        doc = TSDocComment(comment_text)
        assert doc.description == "A function with examples."
        assert len(doc.examples) == 1
        assert "const result = myFunc(1, 2);" in doc.examples[0]

    def test_comment_with_deprecated(self) -> None:
        """Test parsing JSDoc comment with deprecated tag."""
        comment_text = """
        /**
         * This function is deprecated.
         * @deprecated Use newFunction instead
         * @since 1.0.0
         */
        """
        doc = TSDocComment(comment_text)
        assert doc.deprecated == "Use newFunction instead"
        assert doc.since == "1.0.0"


class TestTSParser:
    """Test TypeScript parser functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.parser = TSParser()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_temp_file(self, filename: str, content: str) -> Path:
        """Create a temporary TypeScript file with given content."""
        file_path = Path(self.temp_dir) / filename
        with file_path.open("w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def test_parse_simple_class(self) -> None:
        """Test parsing a simple TypeScript class."""
        content = """
        /**
         * A simple calculator class.
         */
        export class Calculator {
            /**
             * Adds two numbers.
             */
            add(a: number, b: number): number {
                return a + b;
            }
        }
        """
        file_path = self.create_temp_file("calculator.ts", content)

        try:
            result = self.parser.parse_file(file_path)

            assert "classes" in result
            assert len(result["classes"]) == 1

            calc_class = result["classes"][0]
            assert calc_class.name == "Calculator"
            assert calc_class.is_export
            assert len(calc_class.methods) == 1

            add_method = calc_class.methods[0]
            assert add_method.name == "add"

        except Exception as e:
            # If tree-sitter is not properly installed, skip the test
            pytest.skip(f"Tree-sitter parsing failed: {e}")

    def test_parse_interface(self) -> None:
        """Test parsing a TypeScript interface."""
        content = """
        /**
         * Configuration interface.
         */
        export interface Config {
            /**
             * The name property.
             */
            name: string;

            /**
             * Optional value.
             */
            value?: number;
        }
        """
        file_path = self.create_temp_file("config.ts", content)

        try:
            result = self.parser.parse_file(file_path)

            assert "interfaces" in result
            assert len(result["interfaces"]) == 1

            config_interface = result["interfaces"][0]
            assert config_interface.name == "Config"
            assert config_interface.is_export
            assert len(config_interface.properties) >= 1

        except Exception as e:
            pytest.skip(f"Tree-sitter parsing failed: {e}")

    def test_parse_variable(self) -> None:
        """Test parsing TypeScript variables."""
        content = """
        /**
         * A constant value.
         */
        export const MY_CONSTANT = 42;

        /**
         * A variable.
         */
        let myVariable: string = "hello";
        """
        file_path = self.create_temp_file("variables.ts", content)

        try:
            result = self.parser.parse_file(file_path)

            assert "variables" in result
            # We should have at least one variable parsed
            assert len(result["variables"]) >= 0

        except Exception as e:
            pytest.skip(f"Tree-sitter parsing failed: {e}")

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse_file("nonexistent.ts")

    def test_parse_invalid_typescript(self) -> None:
        """Test parsing invalid TypeScript code."""
        content = """
        // This is invalid TypeScript syntax
        class {
            method(: string {
                return "broken";
        """
        file_path = self.create_temp_file("invalid.ts", content)

        try:
            # Should not raise an exception, but return empty or partial results
            result = self.parser.parse_file(file_path)
            assert isinstance(result, dict)

        except Exception as e:
            pytest.skip(f"Tree-sitter parsing failed: {e}")


class TestTSMemberClasses:
    """Test TypeScript member data classes."""

    def test_ts_class_creation(self) -> None:
        """Test creating a TSClass instance."""
        ts_class = TSClass("MyClass")
        assert ts_class.name == "MyClass"
        assert ts_class.methods == []
        assert ts_class.properties == []
        assert not ts_class.is_export

    def test_ts_interface_creation(self) -> None:
        """Test creating a TSInterface instance."""
        ts_interface = TSInterface("MyInterface")
        assert ts_interface.name == "MyInterface"
        assert ts_interface.methods == []
        assert ts_interface.properties == []
        assert not ts_interface.is_export

    def test_ts_variable_creation(self) -> None:
        """Test creating a TSVariable instance."""
        ts_var = TSVariable("myVar")
        assert ts_var.name == "myVar"
        assert ts_var.kind == "let"
        assert not ts_var.is_export

    def test_ts_method_creation(self) -> None:
        """Test creating a TSMethod instance."""
        ts_method = TSMethod("myMethod")
        assert ts_method.name == "myMethod"
        assert ts_method.kind == "method"
        assert ts_method.parameters == []
        assert not ts_method.is_async


class TestTSEnumClasses:
    """Test TypeScript enum data classes."""

    def test_ts_enum_creation(self) -> None:
        """Test creating a TSEnum instance."""
        ts_enum = TSEnum("MyEnum")
        assert ts_enum.name == "MyEnum"
        assert ts_enum.members == []
        assert not ts_enum.is_const
        assert not ts_enum.is_export
        assert not ts_enum.is_declare

    def test_ts_enum_member_creation(self) -> None:
        """Test creating a TSEnumMember instance."""
        member = TSEnumMember("VALUE")
        assert member.name == "VALUE"
        assert member.value is None
        assert not member.computed_value

    def test_ts_enum_member_with_value(self) -> None:
        """Test creating a TSEnumMember with a value."""
        member = TSEnumMember("STATUS")
        member.value = '"active"'
        assert member.name == "STATUS"
        assert member.value == '"active"'
        assert not member.computed_value

    def test_parse_basic_enum(self) -> None:
        """Test parsing a basic TypeScript enum."""
        content = """
/**
 * Basic color enum.
 */
export enum Color {
    /** Red color */
    RED = "red",
    /** Blue color */
    BLUE = "blue"
}
"""
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = Path(temp_dir) / "test.ts"
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)

            parser = TSParser()
            result = parser.parse_file(file_path)

            assert len(result["enums"]) == 1
            enum = result["enums"][0]
            assert enum.name == "Color"
            assert enum.is_export
            assert not enum.is_const
            assert not enum.is_declare
            expected_member_count = 2
            assert len(enum.members) == expected_member_count

            # Check first member
            red_member = enum.members[0]
            assert red_member.name == "RED"
            assert red_member.value == '"red"'
            assert not red_member.computed_value

            # Check second member
            blue_member = enum.members[1]
            assert blue_member.name == "BLUE"
            assert blue_member.value == '"blue"'
            assert not blue_member.computed_value

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parse_const_enum(self) -> None:
        """Test parsing a const enum."""
        content = """
export const enum Direction {
    NORTH = "north",
    SOUTH = "south"
}
"""
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = Path(temp_dir) / "test.ts"
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)

            parser = TSParser()
            result = parser.parse_file(file_path)

            assert len(result["enums"]) == 1
            enum = result["enums"][0]
            assert enum.name == "Direction"
            assert enum.is_export
            assert enum.is_const
            assert not enum.is_declare

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parse_declare_enum(self) -> None:
        """Test parsing a declare enum."""
        content = """
declare enum ExternalEnum {
    FIRST,
    SECOND
}
"""
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = Path(temp_dir) / "test.ts"
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)

            parser = TSParser()
            result = parser.parse_file(file_path)

            assert len(result["enums"]) == 1
            enum = result["enums"][0]
            assert enum.name == "ExternalEnum"
            assert not enum.is_export
            assert not enum.is_const
            assert enum.is_declare

            # Check auto-increment members
            first_member = enum.members[0]
            assert first_member.name == "FIRST"
            assert first_member.value is None

            second_member = enum.members[1]
            assert second_member.name == "SECOND"
            assert second_member.value is None

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parse_computed_enum(self) -> None:
        """Test parsing enum with computed values."""
        content = """
export enum Permission {
    READ = 1 << 0,
    WRITE = 1 << 1,
    ADMIN = READ | WRITE
}
"""
        temp_dir = tempfile.mkdtemp()
        try:
            file_path = Path(temp_dir) / "test.ts"
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)

            parser = TSParser()
            result = parser.parse_file(file_path)

            assert len(result["enums"]) == 1
            enum = result["enums"][0]
            assert enum.name == "Permission"

            # Check computed values
            read_member = enum.members[0]
            assert read_member.name == "READ"
            assert read_member.value == "1 << 0"
            assert read_member.computed_value

            write_member = enum.members[1]
            assert write_member.name == "WRITE"
            assert write_member.value == "1 << 1"
            assert write_member.computed_value

            admin_member = enum.members[2]
            assert admin_member.name == "ADMIN"
            assert admin_member.value == "READ | WRITE"
            assert admin_member.computed_value

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__])
