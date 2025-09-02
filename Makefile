# Makefile for TypeScript Sphinx Extension
# Provides common development tasks and commands

.PHONY: help install install-dev clean test test-coverage lint format type-check docs docs-clean docs-serve build upload upload-test pre-commit setup-dev

# Default target
help:
	@echo "TypeScript Sphinx Extension - Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  setup-dev     - Set up development environment"
	@echo "  install       - Install package in development mode"
	@echo "  install-dev   - Install with development dependencies"
	@echo "  clean         - Remove build artifacts and cache files"
	@echo "  test          - Run tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint          - Run linting (flake8)"
	@echo "  format        - Format code (black + isort)"
	@echo "  format-check  - Check code formatting without changes"
	@echo "  type-check    - Run type checking (mypy)"
	@echo "  docs          - Build documentation"
	@echo "  docs-clean    - Clean documentation build"
	@echo "  docs-serve    - Serve documentation locally"
	@echo "  build         - Build distribution packages"
	@echo "  upload-test   - Upload to test PyPI"
	@echo "  upload        - Upload to PyPI"
	@echo "  pre-commit    - Run all pre-commit checks"
	@echo "  check-all     - Run all checks (lint, format-check, type-check, test)"

# Set up development environment
setup-dev:
	@echo "Setting up development environment..."
	python -m pip install --upgrade pip
	pip install -e ".[dev]"
	pre-commit install
	@echo "Development environment ready!"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Clean up build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf docs/_build/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.orig" -delete
	@echo "Clean complete!"

# Testing targets
test:
	@echo "Running tests..."
	pytest

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=ts_sphinx --cov-report=term-missing --cov-report=html

# Code quality targets
lint:
	@echo "Running linting..."
	flake8 src/ tests/

format:
	@echo "Formatting code..."
	black src/ tests/
	isort src/ tests/

format-check:
	@echo "Checking code formatting..."
	black --check src/ tests/
	isort --check-only src/ tests/

type-check:
	@echo "Running type checking..."
	mypy src/ts_sphinx

# Documentation targets
docs:
	@echo "Building documentation..."
	cd docs && make html

docs-clean:
	@echo "Cleaning documentation..."
	cd docs && make clean

docs-serve: docs
	@echo "Serving documentation at http://localhost:8000"
	cd docs/_build/html && uv run python -m http.server 8000

# Build and distribution targets
build: clean
	@echo "Building distribution packages..."
	python -m build

upload-test: build
	@echo "Uploading to test PyPI..."
	python -m twine upload --repository testpypi dist/*

upload: build
	@echo "Uploading to PyPI..."
	python -m twine upload dist/*

# Pre-commit and comprehensive checking
pre-commit:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

check-all: lint format-check type-check test
	@echo "All checks completed!"

# Development workflow targets
dev-check: format lint type-check test
	@echo "Development checks completed!"

release-check: clean format-check lint type-check test docs build
	@echo "Release checks completed!"

# Tree-sitter setup (if needed)
setup-tree-sitter:
	@echo "Setting up Tree-sitter..."
	python -c "from tree_sitter import Language; print('Tree-sitter available')" || \
	(echo "Installing Tree-sitter dependencies..." && pip install tree-sitter tree-sitter-typescript)

# Example usage targets
run-example:
	@echo "Running example documentation build..."
	cd docs && make html
	@echo "Example documentation built in docs/_build/html/"

test-example:
	@echo "Testing with example TypeScript files..."
	python -c "from ts_sphinx.parser import TSParser; p = TSParser(); print('Parser initialized successfully')"

# Debug and development helpers
debug-parser:
	@echo "Testing TypeScript parser with example file..."
	python -c "from ts_sphinx.parser import TSParser; import pprint; p = TSParser(); result = p.parse_file('examples/calculator.ts'); pprint.pprint(result)"

debug-extension:
	@echo "Testing Sphinx extension loading..."
	python -c "from ts_sphinx import setup; print('Extension loaded successfully')"

# Version management
version:
	@echo "Current version:"
	@python -c "from ts_sphinx import __version__; print(__version__)"

bump-version:
	@echo "Please update version manually in:"
	@echo "  - src/ts_sphinx/__init__.py"
	@echo "  - pyproject.toml"
	@echo "  - setup.py"

# Git helpers
git-clean:
	git clean -fdx

git-reset:
	git reset --hard HEAD

# CI simulation
ci-test: clean setup-tree-sitter format-check lint type-check test
	@echo "CI simulation completed!"
