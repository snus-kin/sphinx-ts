# TypeScript Sphinx Extension - Formatting Alignment

## Overview

This document describes the formatting alignment improvements made to the TypeScript Sphinx extension to ensure consistent documentation structure across all directive types.

## Problem Statement

The original implementation had formatting inconsistencies between different directive types:

1. **Container Structure**: Data directive used `nodes.section` while others used `addnodes.desc`
2. **Signature Creation**: Different approaches to creating and formatting signatures
3. **Content Organization**: Varying methods for organizing sub-elements
4. **RST Parsing**: Inconsistent robustness in RST content parsing
5. **CSS Classes**: Non-uniform CSS class naming and application
6. **Error Handling**: Different fallback mechanisms across directives

## Solution

### Shared Formatting Utilities

Added three core standardization methods to the base `TSAutoDirective` class:

#### 1. `_create_standard_desc_node()`

Creates consistent descriptor node structure for all object types:

```python
def _create_standard_desc_node(
    self,
    objtype: str,
    name: str,
    parent_name: str | None = None,
) -> tuple[addnodes.desc, addnodes.desc_signature, addnodes.desc_content]:
```

**Features:**
- Uniform `addnodes.desc` structure across all directives
- Consistent CSS classes: `sig-object ts ts-{objtype}`
- Standardized ID generation: `{objtype}-{qualified_name}`
- Returns tuple for further customization

#### 2. `_add_standard_doc_content()`

Provides consistent documentation content parsing and error handling:

```python
def _add_standard_doc_content(
    self,
    content_node: addnodes.desc_content,
    doc_comment: TSDocComment | None,
    skip_params: bool = False,
    skip_returns: bool = False,
    skip_examples: bool = False,
) -> None:
```

**Features:**
- Robust RST parsing with fallback to plain text
- Consistent error handling and logging
- Selective content inclusion via skip parameters
- Uses Sphinx's native content parsing mechanism

#### 3. `_create_standard_signature()`

Creates uniform signature formatting with modifiers and type information:

```python
def _create_standard_signature(
    self,
    sig_node: addnodes.desc_signature,
    name: str,
    annotation: str = "",
    type_params: list[str] | None = None,
    extends: list[str] | None = None,
    modifiers: list[str] | None = None,
) -> None:
```

**Features:**
- Consistent modifier handling (export, declare, const, etc.)
- Uniform type parameter and inheritance clause formatting
- Standardized annotation placement

## Directive-Specific Improvements

### Class Directive (`TSAutoClassDirective`)

**Before:**
- Manual `addnodes.desc` creation
- Custom RST parsing with try/catch blocks
- Inconsistent signature formatting

**After:**
- Uses `_create_standard_desc_node()` for structure
- Uses `_create_standard_signature()` for class signature
- Uses `_add_standard_doc_content()` for documentation

### Interface Directive (`TSAutoInterfaceDirective`)

**Before:**
- Similar to class but with type parameter handling differences
- Custom extends clause formatting

**After:**
- Unified with class directive approach
- Type parameters and extends handled by `_create_standard_signature()`

### Enum Directive (`TSAutoEnumDirective`)

**Before:**
- Complex modifier handling (export, declare, const)
- Section-based member organization
- Custom signature creation for members

**After:**
- Standardized modifier collection and application
- Uses shared utilities for both enum and member formatting
- Consistent member signature structure

### Data Directive (`TSAutoDataDirective`)

**Before:**
- Used `nodes.section` instead of `addnodes.desc`
- Different structure for functions, variables, and type aliases
- Manual title creation

**After:**
- Unified `addnodes.desc` structure for all data types
- Consistent handling of variables, functions, and type aliases
- Standardized signature creation with type annotations

## Benefits Achieved

### 1. Structural Consistency
- All directives now use `addnodes.desc` structure
- Uniform CSS class application: `sig-object ts ts-{type}`
- Consistent ID generation patterns

### 2. Error Resilience
- Standardized error handling across all directives
- Consistent fallback mechanisms
- Improved logging for debugging

### 3. Maintainability
- Shared utilities reduce code duplication
- Changes to formatting can be made in one place
- Easier to add new directive types

### 4. Documentation Quality
- More robust RST parsing
- Consistent rendering across directive types
- Better handling of complex documentation features

## Testing

All existing tests continue to pass, ensuring backward compatibility:

```bash
pytest tests/test_directives.py -v  # 28/28 tests passed
pytest tests/ -v                    # 83/83 tests passed
```

## Usage Examples

### Before (Data Directive)
```python
# Created inconsistent section-based structure
var_node = nodes.section(ids=[f"variable-{variable_name}"])
title = nodes.title(text=signature)
var_node.append(title)
```

### After (Data Directive)
```python
# Uses standardized desc structure
var_node, var_sig, var_content = self._create_standard_desc_node(
    "data", variable_name
)
self._create_standard_signature(var_sig, variable_name, modifiers=modifiers)
self._add_standard_doc_content(var_content, doc_comment)
```

## Impact on Generated Documentation

- **CSS Consistency**: All documented items now use consistent CSS classes
- **Cross-References**: Uniform ID generation improves cross-referencing
- **Theming**: Better support for custom themes due to consistent structure
- **Accessibility**: More predictable HTML structure for screen readers

## Future Enhancements

The standardized utilities provide a foundation for future improvements:

1. **Advanced Formatting**: Easy to add new signature components
2. **Custom Themes**: Consistent structure simplifies theme development
3. **Export Features**: Uniform structure enables better export functionality
4. **Performance**: Shared utilities can be optimized in one location

## Domain Layer Fixes

During the formatting alignment, an additional issue was discovered and fixed in the domain layer that was preventing proper method name styling:

### Problem
The TypeScript domain handlers were using `addnodes.desc_name` instead of `addnodes.desc_sig_name` for callable elements (methods, properties, functions), which prevented the red text styling from being applied.

### Solution
Updated domain handlers to use the correct node types:

**Fixed Classes:**
- `TSMethod.handle_signature()` - Now uses `desc_sig_name` for method names
- `TSProperty.handle_signature()` - Now uses `desc_sig_name` for property names  
- `TSFunction.handle_signature()` - Now uses `desc_sig_name` for function names

**Result:**
- ✅ Method names now display in red text
- ✅ Property names now display in red text
- ✅ Function names now display in red text
- ✅ Class/interface/enum names remain in normal text (appropriate)

This fix ensures that the Sphinx CSS can properly style callable elements with the distinctive red coloring that users expect.

## Conclusion

The formatting alignment successfully unifies the documentation structure across all TypeScript directive types while maintaining full backward compatibility. Additionally, the domain layer fixes ensure proper styling of method, property, and function names with the expected red text coloring. The solution provides a solid foundation for future enhancements and significantly improves both the maintainability of the codebase and the visual consistency of the generated documentation.