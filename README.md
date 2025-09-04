# TypeScript Sphinx Extension

A Sphinx extension that provides autodoc-like functionality for TypeScript files using Tree-sitter for parsing. This extension allows you to automatically generate documentation for TypeScript classes, interfaces, and variables from your source code, similar to Python's autodoc.

## Features

- **Automatic Documentation Generation**: Extract documentation from TypeScript source files
- **JSDoc Support**: Parse and render JSDoc comments as reStructuredText
- **Multiple Directives**: Support for `ts:autoclass`, `ts:autointerface`, `ts:autoenum`, and `ts:autodata`
- **Tree-sitter Parsing**: Robust TypeScript parsing using Tree-sitter
- **Sphinx Integration**: Full integration with Sphinx's cross-referencing and indexing systems
- **Type Information**: Display TypeScript type annotations and signatures

## Installation

### Prerequisites

- Python 3.9 or higher
- Sphinx 5.0.0 or higher

### Install from Source

```bash
git clone https://github.com/yourusername/ts-sphinx.git
cd ts-sphinx
pip install -e .
```

### Dependencies

The extension automatically installs the following dependencies:

- `sphinx>=5.0.0`
- `tree-sitter>=0.20.0`
- `tree-sitter-typescript>=0.20.0`
- `docutils>=0.17`

## Configuration

Add the extension to your Sphinx `conf.py`:

```python
extensions = [
    'sphinx_ts',
    # other extensions...
]

# TypeScript Sphinx configuration
sphinx_ts_src_dirs = ['src', 'lib']  # Directories to scan for TypeScript files
sphinx_ts_exclude_patterns = ['**/*.test.ts', '**/*.spec.ts']  # Files to exclude
sphinx_ts_include_private = False  # Include private members
sphinx_ts_include_inherited = True  # Include inherited members
```

## Usage

### Available Directives

#### `ts:autoclass`

Automatically document a TypeScript class:

```rst
.. ts:autoclass:: MyClass
   :members:
   :undoc-members:
   :show-inheritance:
```

#### `ts:autointerface`

Automatically document a TypeScript interface:

```rst
.. ts:autointerface:: MyInterface
   :members:
   :undoc-members:
```

#### `ts:autoenum`

Automatically document a TypeScript enum:

```rst
.. ts:autoenum:: MyEnum
   :members:
   :undoc-members:
```

#### `ts:autodata`

Automatically document TypeScript variables and constants:

```rst
.. ts:autodata:: myVariable
.. ts:autodata:: MY_CONSTANT
```

### Directive Options

All auto-directives support the following options:

- `:members:` - Include all members
- `:undoc-members:` - Include members without documentation
- `:show-inheritance:` - Show inheritance relationships (classes only)
- `:member-order:` - Order of members (`alphabetical`, `groupwise`, or `bysource`)
- `:exclude-members:` - Comma-separated list of members to exclude
- `:private-members:` - Include private members
- `:special-members:` - Include special members
- `:no-index:` - Don't add to the general index

### Cross-References

The extension provides several roles for cross-referencing:

```rst
:ts:class:`MyClass`
:ts:interface:`MyInterface`
:ts:enum:`MyEnum`
:ts:meth:`MyClass.myMethod`
:ts:prop:`MyClass.myProperty`
:ts:func:`myFunction`
:ts:var:`myVariable`
```

## Example

Given the following TypeScript file (`src/example.ts`):

```typescript
/**
 * A sample class demonstrating the documentation features.
 *
 * @example
 * ```typescript
 * const calc = new Calculator();
 * const result = calc.add(5, 3);
 * console.log(result); // 8
 * ```
 */
export class Calculator {
    /**
     * The current value stored in the calculator.
     */
    public value: number = 0;

    /**
     * Adds two numbers together.
     *
     * @param a The first number
     * @param b The second number
     * @returns The sum of a and b
     * @example
     * ```typescript
     * calc.add(2, 3); // returns 5
     * ```
     */
    public add(a: number, b: number): number {
        return a + b;
    }

    /**
     * Multiplies two numbers.
     *
     * @param a The first number
     * @param b The second number
     * @returns The product of a and b
     */
    public multiply(a: number, b: number): number {
        return a * b;
    }
}

/**
 * Configuration interface for the calculator.
 */
export interface CalculatorConfig {
    /**
     * The precision for decimal calculations.
     */
    precision: number;

    /**
     * Whether to round results.
     */
    roundResults?: boolean;
}

/**
 * Default configuration for the calculator.
 */
export const DEFAULT_CONFIG: CalculatorConfig = {
    precision: 2,
    roundResults: true
};

/**
 * Status levels for calculator operations.
 */
export enum CalculatorStatus {
    /** Operation completed successfully */
    SUCCESS = "success",
    /** Warning during calculation */
    WARNING = "warning", 
    /** Error occurred */
    ERROR = "error"
}
```

You can document it in your RST file:

```rst
Calculator Module
=================

.. ts:autoclass:: Calculator
   :members:
   :undoc-members:

Configuration
-------------

.. ts:autointerface:: CalculatorConfig
   :members:

.. ts:autoenum:: CalculatorStatus
   :members:

.. ts:autodata:: DEFAULT_CONFIG
```

This will generate comprehensive documentation including:

- Class description with examples
- Method signatures with parameter and return type information
- Property documentation
- Interface member documentation
- Variable type and value information

## JSDoc Support

The extension supports standard JSDoc tags:

- `@param {type} name description` - Parameter documentation
- `@returns description` or `@return description` - Return value documentation
- `@example` - Code examples
- `@since version` - Version information
- `@deprecated message` - Deprecation notices
- Custom tags are also preserved

## Advanced Features

### Type Information

The extension automatically extracts and displays:

- Parameter types and default values
- Return types
- Property types
- Generic type parameters
- Union and intersection types

### Inheritance

For classes, the extension shows:

- Base class inheritance
- Implemented interfaces
- Inherited methods and properties

### Source Links

Each documented item includes a reference to its source file for easy navigation.

## Development

### Setting up Development Environment

```bash
git clone https://github.com/yourusername/ts-sphinx.git
cd ts-sphinx
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 0.1.0

- Initial release
- Support for `ts:autoclass`, `ts:autointerface`, `ts:autoenum`, and `ts:autodata` directives
- JSDoc comment parsing
- Tree-sitter based TypeScript parsing
- Full Sphinx domain integration
- Cross-referencing support
- Enum documentation with member value display

## Acknowledgments

- [Tree-sitter](https://tree-sitter.github.io/) for robust code parsing
- [Sphinx](https://www.sphinx-doc.org/) for the documentation framework
- The Python autodoc extension for inspiration
