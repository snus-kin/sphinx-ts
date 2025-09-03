Usage Guide
===========

This guide shows you how to use the TypeScript Sphinx Extension to automatically generate documentation from your TypeScript source code.

Installation
------------

Install the extension using pip:

.. code-block:: bash

   pip install ts-sphinx

Or for development:

.. code-block:: bash

   git clone https://github.com/yourusername/ts-sphinx.git
   cd ts-sphinx
   pip install -e .

Configuration
-------------

Add the extension to your Sphinx ``conf.py``:

.. code-block:: python

   extensions = [
       'sphinx_ts',
       'sphinx.ext.autodoc',      # Optional: for Python docs too
       'sphinx.ext.viewcode',     # Optional: for source links
       'sphinx.ext.intersphinx',  # Optional: for cross-references
   ]

   # TypeScript Sphinx Extension Configuration
   sphinx_ts_src_dirs = ['../examples', '../src']
   sphinx_ts_exclude_patterns = [
       '**/*.test.ts',
       '**/*.spec.ts',
       '**/node_modules/**',
       '**/*.d.ts'
   ]
   sphinx_ts_include_private = False
   sphinx_ts_include_inherited = True

Configuration Options
~~~~~~~~~~~~~~~~~~~~

.. confval:: sphinx_ts_src_dirs

   List of directories to scan for TypeScript files (relative to ``conf.py``).

   **Default:** ``[]``

   **Example:** ``['../src', '../lib', '../types']``

.. confval:: sphinx_ts_exclude_patterns

   List of glob patterns for files to exclude from parsing.

   **Default:** ``[]``

   **Example:** ``['**/*.test.ts', '**/*.spec.ts', '**/node_modules/**']``

.. confval:: sphinx_ts_include_private

   Whether to include private members in documentation.

   **Default:** ``False``

.. confval:: sphinx_ts_include_inherited

   Whether to include inherited members in class documentation.

   **Default:** ``True``

Available Directives
-------------------

The extension provides three main auto-documentation directives:

ts:autoclass
~~~~~~~~~~~~

Automatically documents TypeScript classes:

.. code-block:: rst

   .. ts:autoclass:: Calculator
      :members:
      :undoc-members:
      :show-inheritance:

**Options:**

* ``:members:`` - Include all members
* ``:undoc-members:`` - Include members without JSDoc comments
* ``:show-inheritance:`` - Show inheritance relationships
* ``:exclude-members:`` - Comma-separated list of members to exclude
* ``:member-order:`` - Order of members (``alphabetical``, ``groupwise``, or ``bysource``)
* ``:private-members:`` - Include private members
* ``:no-index:`` - Don't add to the general index

ts:autointerface
~~~~~~~~~~~~~~~~

Automatically documents TypeScript interfaces:

.. code-block:: rst

   .. ts:autointerface:: CalculatorConfig
      :members:
      :undoc-members:

**Options:** Same as ``ts:autoclass`` except ``:show-inheritance:``

ts:autodata
~~~~~~~~~~~

Automatically documents TypeScript variables and constants:

.. code-block:: rst

   .. ts:autodata:: DEFAULT_CONFIG
   .. ts:autodata:: MATH_CONSTANTS

Cross-References
---------------

The extension provides several roles for cross-referencing TypeScript objects:

Basic References
~~~~~~~~~~~~~~~

.. code-block:: rst

   :ts:class:`Calculator`
   :ts:interface:`CalculatorConfig`
   :ts:meth:`Calculator.add`
   :ts:prop:`Calculator.memory`
   :ts:func:`isSafeInteger`
   :ts:var:`DEFAULT_CONFIG`

Generic Reference
~~~~~~~~~~~~~~~~

Use the generic ``:ts:obj:`` role when you're not sure of the object type:

.. code-block:: rst

   :ts:obj:`Calculator`
   :ts:obj:`CalculatorConfig`

Complete Example
---------------

Here's a complete example showing how to document a TypeScript project:

Directory Structure
~~~~~~~~~~~~~~~~~~

.. code-block::

   my-project/
   ├── docs/
   │   ├── conf.py
   │   ├── index.rst
   │   └── api.rst
   └── src/
       ├── calculator.ts
       └── types.ts

TypeScript Source (src/calculator.ts)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: typescript

   /**
    * A comprehensive calculator class demonstrating various TypeScript features.
    *
    * @example
    * ```typescript
    * const calc = new Calculator();
    * const result = calc.add(5, 3);
    * console.log(result); // 8
    * ```
    *
    * @since 1.0.0
    */
   export class Calculator {
       /**
        * The current value stored in the calculator's memory.
        */
       private _memory: number = 0;

       /**
        * Gets the current memory value.
        *
        * @returns The current value in memory
        */
       get memory(): number {
           return this._memory;
       }

       /**
        * Adds two numbers together.
        *
        * @param a The first number to add
        * @param b The second number to add
        * @returns The sum of a and b
        * @example
        * ```typescript
        * const result = calc.add(2, 3);
        * console.log(result); // 5
        * ```
        */
       public add(a: number, b: number): number {
           return a + b;
       }

       /**
        * Divides the first number by the second.
        *
        * @param a The dividend
        * @param b The divisor
        * @returns The quotient of a divided by b
        * @throws Error when dividing by zero
        */
       public divide(a: number, b: number): number {
           if (b === 0) {
               throw new Error("Division by zero is not allowed");
           }
           return a / b;
       }
   }

   /**
    * Configuration interface for the Calculator class.
    */
   export interface CalculatorConfig {
       /**
        * Number of decimal places to round results to.
        *
        * @default 2
        */
       precision: number;

       /**
        * Whether to automatically round calculation results.
        *
        * @default true
        */
       roundResults?: boolean;
   }

   /**
    * Default configuration values for new Calculator instances.
    */
   export const DEFAULT_CONFIG: CalculatorConfig = {
       precision: 2,
       roundResults: true
   };

Documentation File (docs/api.rst)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

   API Reference
   =============

   Calculator Class
   ---------------

   .. ts:autoclass:: Calculator
      :members:
      :undoc-members:

   Configuration
   -------------

   .. ts:autointerface:: CalculatorConfig
      :members:

   Constants
   ---------

   .. ts:autodata:: DEFAULT_CONFIG

   Examples
   --------

   Basic Usage
   ~~~~~~~~~~~

   Here's how to use the :ts:class:`Calculator`:

   .. code-block:: typescript

      import { Calculator, DEFAULT_CONFIG } from './calculator';

      const calc = new Calculator(DEFAULT_CONFIG);
      const result = calc.add(10, 5);

   You can also reference specific methods like :ts:meth:`Calculator.add`
   or properties like :ts:prop:`Calculator.memory`.

Advanced Usage
-------------

Custom Member Selection
~~~~~~~~~~~~~~~~~~~~~~

You can control which members are documented:

.. code-block:: rst

   .. ts:autoclass:: Calculator
      :members: add, subtract, multiply
      :exclude-members: _private_method

Member Ordering
~~~~~~~~~~~~~~

Control the order of documented members:

.. code-block:: rst

   .. ts:autoclass:: Calculator
      :members:
      :member-order: alphabetical

Include Private Members
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: rst

   .. ts:autoclass:: Calculator
      :members:
      :private-members:

Multiple Source Directories
~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure multiple source directories in ``conf.py``:

.. code-block:: python

   sphinx_ts_src_dirs = [
       '../src',
       '../lib',
       '../types',
       '../utils'
   ]

Exclude Patterns
~~~~~~~~~~~~~~~

Exclude specific files or patterns:

.. code-block:: python

   sphinx_ts_exclude_patterns = [
       '**/*.test.ts',           # Test files
       '**/*.spec.ts',           # Spec files
       '**/*.d.ts',              # Type declarations
       '**/node_modules/**',     # Dependencies
       'src/internal/**'         # Internal modules
   ]

JSDoc Tag Support
----------------

The extension recognizes and renders these JSDoc tags:

Standard Tags
~~~~~~~~~~~~

* ``@param {type} name description`` - Parameter documentation
* ``@returns description`` or ``@return description`` - Return value documentation
* ``@throws description`` or ``@exception description`` - Exception documentation
* ``@example`` - Code examples
* ``@since version`` - Version information
* ``@deprecated message`` - Deprecation notices

Custom Tags
~~~~~~~~~~

Custom JSDoc tags are preserved and rendered:

.. code-block:: typescript

   /**
    * A special function.
    *
    * @customtag This will be preserved
    * @author John Doe
    * @version 1.2.3
    */
   function specialFunction() {}

Troubleshooting
--------------

Tree-sitter Not Found
~~~~~~~~~~~~~~~~~~~~

If you get import errors related to Tree-sitter:

.. code-block:: bash

   pip install tree-sitter tree-sitter-typescript

TypeScript Files Not Found
~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure your ``sphinx_ts_src_dirs`` paths are correct relative to ``conf.py``:

.. code-block:: python

   # If your structure is:
   # project/
   #   docs/conf.py
   #   src/file.ts

   sphinx_ts_src_dirs = ['../src']

No Documentation Generated
~~~~~~~~~~~~~~~~~~~~~~~~~~

Check that:

1. TypeScript files contain proper JSDoc comments
2. Classes/interfaces are exported
3. File paths are not excluded by ``sphinx_ts_exclude_patterns``
4. TypeScript syntax is valid

Performance Tips
---------------

For large codebases:

1. Use specific source directories instead of scanning everything
2. Use exclude patterns to skip test files and dependencies
3. Consider using ``:no-index:`` for internal APIs
4. Enable parallel builds in Sphinx configuration

.. code-block:: python

   # In conf.py
   sphinx_build_parallel = 4  # Use 4 parallel processes
