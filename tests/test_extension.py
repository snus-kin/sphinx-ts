"""Tests for the main TypeScript Sphinx extension setup and integration."""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from sphinx_ts import setup
from sphinx_ts.directives import (
    TSAutoClassDirective,
    TSAutoDataDirective,
    TSAutoInterfaceDirective,
)

import ts_sphinx
from ts_sphinx import setup
from ts_sphinx.directives import (
    TSAutoClassDirective,
    TSAutoDataDirective,
    TSAutoInterfaceDirective,
)
from ts_sphinx.domain import TypeScriptDomain
from ts_sphinx.parser import (
    TSClass,
    TSDocComment,
    TSInterface,
    TSMethod,
    TSParser,
    TSProperty,
    TSVariable,
)

# Test constants
EXPECTED_DIRECTIVES_COUNT = 3
EXPECTED_CONFIG_VALUES_COUNT = 4


class MockSphinxApp:
    """Mock Sphinx application for testing."""

    def __init__(self) -> None:
        self.domains = {}
        self.directives = {}
        self.config_values = {}
        self.added_domains = []
        self.added_directives = []
        self.added_config_values = []

    def add_domain(self, domain_class: type) -> None:
        """Mock add_domain method."""
        self.added_domains.append(domain_class)
        self.domains[domain_class.name] = domain_class

    def add_directive(self, name: str, directive_class: type) -> None:
        """Mock add_directive method."""
        self.added_directives.append((name, directive_class))
        self.directives[name] = directive_class

    def add_config_value(
        self,
        name: str,
        default: Any,  # noqa: ANN401
        rebuild: str,
        types: Any = None,  # noqa: ANN401
    ) -> None:
        """Mock add_config_value method."""
        self.added_config_values.append((name, default, rebuild, types))
        self.config_values[name] = (default, rebuild, types)


class TestExtensionSetup:
    """Test the main extension setup function."""

    def test_setup_function_exists(self) -> None:
        """Test that the setup function exists and is callable."""
        assert hasattr(ts_sphinx, "setup")
        assert callable(ts_sphinx.setup)

    def test_setup_returns_metadata(self) -> None:
        """Test that setup function returns proper metadata."""
        app = MockSphinxApp()
        result = setup(app)

        assert isinstance(result, dict)
        assert "version" in result
        assert "parallel_read_safe" in result
        assert "parallel_write_safe" in result
        assert result["version"] == "0.1.0"
        assert result["parallel_read_safe"] is True
        assert result["parallel_write_safe"] is True

    def test_setup_adds_domain(self) -> None:
        """Test that setup function adds the TypeScript domain."""
        app = MockSphinxApp()
        setup(app)

        assert len(app.added_domains) == 1
        assert app.added_domains[0] == TypeScriptDomain
        assert TypeScriptDomain in app.domains.values()

    def test_setup_adds_directives(self) -> None:
        """Test that setup function adds all required directives."""
        app = MockSphinxApp()
        setup(app)

        expected_directives = [
            ("ts:autoclass", TSAutoClassDirective),
            ("ts:autointerface", TSAutoInterfaceDirective),
            ("ts:autodata", TSAutoDataDirective),
        ]

        assert len(app.added_directives) == EXPECTED_DIRECTIVES_COUNT
        for expected_name, expected_class in expected_directives:
            assert (expected_name, expected_class) in app.added_directives

    def test_setup_adds_config_values(self) -> None:
        """Test that setup function adds all configuration values."""
        app = MockSphinxApp()
        setup(app)

        expected_configs = [
            ("ts_sphinx_src_dirs", [], "env", [list]),
            ("ts_sphinx_exclude_patterns", [], "env", [list]),
            ("ts_sphinx_include_private", False, "env", [bool]),
            ("ts_sphinx_include_inherited", True, "env", [bool]),
        ]

        assert len(app.added_config_values) == EXPECTED_CONFIG_VALUES_COUNT
        for expected_config in expected_configs:
            assert expected_config in app.added_config_values

    def test_setup_with_real_sphinx_app_mock(self) -> None:
        """Test setup with a more realistic Sphinx app mock."""
        with patch("sphinx.application.Sphinx") as mock_app_class:
            mock_app = mock_app_class.return_value
            mock_app.add_domain = Mock()
            mock_app.add_directive = Mock()
            mock_app.add_config_value = Mock()

            result = setup(mock_app)

            # Verify domain was added
            mock_app.add_domain.assert_called_once_with(TypeScriptDomain)

            # Verify directives were added
            count = EXPECTED_DIRECTIVES_COUNT
            assert mock_app.add_directive.call_count == count
            directive_calls = mock_app.add_directive.call_args_list
            directive_names = [call[0][0] for call in directive_calls]
            assert "ts:autoclass" in directive_names
            assert "ts:autointerface" in directive_names
            assert "ts:autodata" in directive_names

            # Verify config values were added
            expected_config_count = EXPECTED_CONFIG_VALUES_COUNT
            assert mock_app.add_config_value.call_count == expected_config_count
            config_calls = mock_app.add_config_value.call_args_list
            config_names = [call[0][0] for call in config_calls]
            assert "ts_sphinx_src_dirs" in config_names
            assert "ts_sphinx_exclude_patterns" in config_names
            assert "ts_sphinx_include_private" in config_names
            assert "ts_sphinx_include_inherited" in config_names

            # Verify return value
            assert isinstance(result, dict)
            assert result["version"] == "0.1.0"


class TestExtensionMetadata:
    """Test extension metadata and version information."""

    def test_extension_has_version(self) -> None:
        """Test that extension has version information."""
        assert hasattr(ts_sphinx, "__version__")
        assert isinstance(ts_sphinx.__version__, str)
        assert len(ts_sphinx.__version__) > 0

    def test_version_consistency(self) -> None:
        """Test that version is consistent between setup and __version__."""
        app = MockSphinxApp()
        result = setup(app)

        assert result["version"] == ts_sphinx.__version__

    def test_extension_has_docstring(self) -> None:
        """Test that extension module has proper documentation."""
        assert ts_sphinx.__doc__ is not None
        assert len(ts_sphinx.__doc__.strip()) > 0
        assert "TypeScript Sphinx Extension" in ts_sphinx.__doc__


class TestExtensionImports:
    """Test that all necessary components can be imported."""

    def test_can_import_main_components(self) -> None:
        """Test that main components can be imported."""

        # Verify they are the expected types
        assert callable(setup)
        assert issubclass(TypeScriptDomain, object)
        assert issubclass(TSAutoClassDirective, object)
        assert issubclass(TSAutoInterfaceDirective, object)
        assert issubclass(TSAutoDataDirective, object)
        assert issubclass(TSParser, object)

    def test_can_import_parser_components(self) -> None:
        """Test that parser components can be imported."""

        # Verify they can be instantiated
        doc_comment = TSDocComment("/** Test comment */")
        ts_class = TSClass("TestClass")
        ts_interface = TSInterface("TestInterface")
        ts_variable = TSVariable("testVar")
        ts_method = TSMethod("testMethod")
        ts_property = TSProperty("testProp")

        assert "Test comment" in doc_comment.description
        assert ts_class.name == "TestClass"
        assert ts_interface.name == "TestInterface"
        assert ts_variable.name == "testVar"
        assert ts_method.name == "testMethod"
        assert ts_property.name == "testProp"


class TestConfigurationDefaults:
    """Test default configuration values."""

    def test_default_src_dirs(self) -> None:
        """Test default source directories configuration."""
        app = MockSphinxApp()
        setup(app)

        src_dirs_config = next(
            (
                config
                for config in app.added_config_values
                if config[0] == "ts_sphinx_src_dirs"
            ),
            None,
        )

        assert src_dirs_config is not None
        assert src_dirs_config[1] == []  # Default value
        assert src_dirs_config[2] == "env"  # Rebuild type
        assert src_dirs_config[3] == [list]  # Type annotation

    def test_default_exclude_patterns(self) -> None:
        """Test default exclude patterns configuration."""
        app = MockSphinxApp()
        setup(app)

        exclude_config = next(
            (
                config
                for config in app.added_config_values
                if config[0] == "ts_sphinx_exclude_patterns"
            ),
            None,
        )

        assert exclude_config is not None
        assert exclude_config[1] == []  # Default value
        assert exclude_config[2] == "env"  # Rebuild type
        assert exclude_config[3] == [list]  # Type annotation

    def test_default_include_private(self) -> None:
        """Test default include private configuration."""
        app = MockSphinxApp()
        setup(app)

        private_config = next(
            (
                config
                for config in app.added_config_values
                if config[0] == "ts_sphinx_include_private"
            ),
            None,
        )

        assert private_config is not None
        assert private_config[1] is False  # Default value
        assert private_config[2] == "env"  # Rebuild type
        assert private_config[3] == [bool]  # Type annotation

    def test_default_include_inherited(self) -> None:
        """Test default include inherited configuration."""
        app = MockSphinxApp()
        setup(app)

        inherited_config = next(
            (
                config
                for config in app.added_config_values
                if config[0] == "ts_sphinx_include_inherited"
            ),
            None,
        )

        assert inherited_config is not None
        assert inherited_config[1] is True  # Default value
        assert inherited_config[2] == "env"  # Rebuild type
        assert inherited_config[3] == [bool]  # Type annotation


class TestExtensionCompatibility:
    """Test extension compatibility features."""

    def test_parallel_read_safe(self) -> None:
        """Test that extension declares parallel read safety."""
        app = MockSphinxApp()
        result = setup(app)

        assert result.get("parallel_read_safe") is True

    def test_parallel_write_safe(self) -> None:
        """Test that extension declares parallel write safety."""
        app = MockSphinxApp()
        result = setup(app)

        assert result.get("parallel_write_safe") is True


class TestExtensionErrorHandling:
    """Test error handling in extension setup."""

    def test_setup_with_none_app(self) -> None:
        """Test setup behavior with None app (should raise AttributeError)."""
        with pytest.raises(AttributeError):
            setup(None)

    def test_setup_with_invalid_app(self) -> None:
        """Test setup behavior with invalid app object."""
        invalid_app = object()  # No required methods

        with pytest.raises(AttributeError):
            setup(invalid_app)

    def test_setup_handles_domain_import_error(self) -> None:
        """Test setup handles domain import errors gracefully."""
        app = MockSphinxApp()

        # Mock app.add_domain to raise an error
        app.add_domain = Mock(side_effect=ImportError("Mock import error"))

        with pytest.raises(ImportError):
            setup(app)

    def test_setup_handles_directive_import_error(self) -> None:
        """Test setup handles directive import errors gracefully."""
        app = MockSphinxApp()

        # Mock app.add_directive to raise an error
        app.add_directive = Mock(side_effect=ImportError("Mock import error"))

        with pytest.raises(ImportError):
            setup(app)


class TestExtensionDocumentation:
    """Test extension documentation and help."""

    def test_module_has_proper_docstring(self) -> None:
        """Test that main module has comprehensive docstring."""
        docstring = ts_sphinx.__doc__

        assert docstring is not None
        assert "TypeScript Sphinx Extension" in docstring
        assert "Tree-sitter" in docstring
        assert "autodoc" in docstring

    def test_setup_function_has_docstring(self) -> None:
        """Test that setup function has docstring."""
        assert setup.__doc__ is not None
        assert len(setup.__doc__.strip()) > 0
        assert "Set up the Sphinx extension" in setup.__doc__


if __name__ == "__main__":
    pytest.main([__file__])
