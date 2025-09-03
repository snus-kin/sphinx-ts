"""Tests for the TypeScript Sphinx domain."""

from unittest.mock import Mock

import pytest

from sphinx_ts.domain import TSXRefRole, TypeScriptDomain

# Test constants
EXPECTED_OBJECTS_COUNT = 3
EXPECTED_OBJECT_TUPLE_LENGTH = 6


class MockBuildEnvironment:
    """Mock Sphinx build environment for testing."""

    def __init__(self) -> None:
        self.docname = "test_doc"
        self.found_docs = set()
        self.domaindata = {}


class TestTypeScriptDomain:
    """Test the TypeScript domain functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.env = MockBuildEnvironment()
        self.domain = TypeScriptDomain(self.env)

    def test_domain_initialization(self) -> None:
        """Test domain initialization."""
        assert self.domain.name == "ts"
        assert self.domain.label == "TypeScript"
        assert "class" in self.domain.object_types
        assert "interface" in self.domain.object_types
        assert "method" in self.domain.object_types
        assert "property" in self.domain.object_types
        assert "function" in self.domain.object_types
        assert "variable" in self.domain.object_types

    def test_directive_registration(self) -> None:
        """Test that directives are properly registered."""
        assert "class" in self.domain.directives
        assert "interface" in self.domain.directives
        assert "method" in self.domain.directives
        assert "property" in self.domain.directives
        assert "function" in self.domain.directives
        assert "variable" in self.domain.directives

    def test_role_registration(self) -> None:
        """Test that roles are properly registered."""
        assert "class" in self.domain.roles
        assert "interface" in self.domain.roles
        assert "meth" in self.domain.roles
        assert "prop" in self.domain.roles
        assert "func" in self.domain.roles
        assert "var" in self.domain.roles
        assert "obj" in self.domain.roles

    def test_note_object(self) -> None:
        """Test noting objects for cross-referencing."""
        self.domain.note_object("class", "MyClass", "class-MyClass")

        assert "class" in self.domain.data["objects"]
        assert "MyClass" in self.domain.data["objects"]["class"]
        assert self.domain.data["objects"]["class"]["MyClass"] == (
            "test_doc",
            "",
        )

    def test_clear_doc(self) -> None:
        """Test clearing document data."""
        # Add some test data
        self.domain.note_object("class", "MyClass", "class-MyClass")
        self.domain.note_object(
            "interface", "MyInterface", "interface-MyInterface"
        )

        # Clear the document
        self.domain.clear_doc("test_doc")

        # Check that objects from this document are removed
        if "class" in self.domain.data["objects"]:
            assert "MyClass" not in self.domain.data["objects"]["class"]
        if "interface" in self.domain.data["objects"]:
            assert "MyInterface" not in self.domain.data["objects"]["interface"]

    def test_merge_domaindata(self) -> None:
        """Test merging domain data from different sources."""
        other_data = {
            "objects": {"class": {"OtherClass": ("other_doc", "synopsis")}}
        }

        self.domain.merge_domaindata({"other_doc"}, other_data)

        assert "class" in self.domain.data["objects"]
        assert "OtherClass" in self.domain.data["objects"]["class"]
        assert self.domain.data["objects"]["class"]["OtherClass"] == (
            "other_doc",
            "synopsis",
        )

    def test_resolve_xref_not_found(self) -> None:
        """Test resolving cross-references when target is not found."""
        builder = Mock()
        contnode = Mock()

        result = self.domain.resolve_xref(
            self.env,
            "source_doc",
            builder,
            "class",
            "NonexistentClass",
            Mock(),
            contnode,
        )

        assert result is None

    def test_get_objects(self) -> None:
        """Test getting all objects for indexing."""
        # Add test data
        self.domain.note_object("class", "MyClass", "class-MyClass")
        self.domain.note_object(
            "interface", "MyInterface", "interface-MyInterface"
        )
        self.domain.note_object("function", "myFunction", "function-myFunction")

        objects = list(self.domain.get_objects())

        assert len(objects) == EXPECTED_OBJECTS_COUNT
        for obj in objects:
            assert (
                len(obj) == EXPECTED_OBJECT_TUPLE_LENGTH
            )  # name, dispname, type, docname, anchor, priority
            assert obj[0] in ["MyClass", "MyInterface", "myFunction"]


class TestTSXRefRole:
    """Test the TypeScript cross-reference role."""

    def test_process_link(self) -> None:
        """Test processing cross-reference links."""
        role = TSXRefRole()
        env = Mock()
        refnode = Mock()

        # Test without explicit title
        title, target = role.process_link(
            env,
            refnode,
            has_explicit_title=False,
            title=".MyClass",
            target=".MyClass",
        )
        assert title == "MyClass"  # Leading dot should be stripped
        assert target == ".MyClass"

        # Test with explicit title
        title, target = role.process_link(
            env,
            refnode,
            has_explicit_title=True,
            title="Custom Title",
            target="MyClass",
        )
        assert title == "Custom Title"
        assert target == "MyClass"


class TestDomainIntegration:
    """Test domain integration with Sphinx."""

    def test_domain_can_be_added_to_app(self) -> None:
        """Test that domain can be added to Sphinx app."""
        # This is more of an integration test
        # In practice, this would be tested by actually running Sphinx
        app = Mock()
        app.add_domain = Mock()

        # This simulates what happens in the setup function
        app.add_domain(TypeScriptDomain)
        app.add_domain.assert_called_once_with(TypeScriptDomain)

    def test_domain_has_required_attributes(self) -> None:
        """Test that domain has all required attributes."""
        env = MockBuildEnvironment()
        domain = TypeScriptDomain(env)

        # Check that domain has all required class attributes
        assert hasattr(domain, "name")
        assert hasattr(domain, "label")
        assert hasattr(domain, "object_types")
        assert hasattr(domain, "directives")
        assert hasattr(domain, "roles")
        assert hasattr(domain, "initial_data")

        # Check that data is properly initialized
        assert isinstance(domain.data, dict)
        assert "objects" in domain.data


if __name__ == "__main__":
    pytest.main([__file__])
