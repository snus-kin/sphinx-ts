# TypeScript Sphinx Extension

A Sphinx extension that provides autodoc-like functionality for TypeScript files
using Tree-sitter for parsing. This extension allows you to automatically
generate documentation for TypeScript classes, interfaces, and variables from
your source code, similar to Python's autodoc.

## Features

- **Automatic Documentation Generation**: Extract documentation from TypeScript source files
- **JSDoc Support**: Parse and render JSDoc comments as reStructuredText
- **Multiple Directives**: Support for `ts:autoclass`, `ts:autointerface`, `ts:autoenum`, and `ts:autodata`
- **Tree-sitter Parsing**: Robust TypeScript parsing using Tree-sitter
- **Sphinx Integration**: Full integration with Sphinx's cross-referencing and indexing systems
- **Type Information**: Display TypeScript type annotations and signatures

## Installation

This project uses uv for package management.

### Install from Source

```bash
git clone https://github.com/yourusername/ts-sphinx.git
cd ts-sphinx
uv sync
```

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
:ts:prop:`MyClass.myProperty`
```


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

### (TODO) Source Links

Each documented item includes a reference to its source file for easy navigation.
