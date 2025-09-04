TypeScript Sphinx Extension Documentation
==========================================

Welcome to the TypeScript Sphinx Extension documentation! This extension provides autodoc-like functionality for TypeScript files using Tree-sitter for parsing, allowing you to automatically generate documentation from your TypeScript source code.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   usage
   examples

Quick Start
-----------

1. Install the extension:

   .. code-block:: bash

      pip install ts-sphinx

2. Add it to your Sphinx ``conf.py``:

   .. code-block:: python

      extensions = [
          'sphinx_ts',
          # other extensions...
      ]

      # Configure source directories
      sphinx_ts_src_dirs = ['src', 'lib']

3. Use the directives in your RST files:

   .. code-block:: rst

      .. ts:autoclass:: MyClass
         :members:

      .. ts:autointerface:: MyInterface
         :members:

      .. ts:autodata:: myConstant

Features
--------

* **Automatic Documentation Generation**: Extract documentation from TypeScript source files
* **JSDoc Support**: Parse and render JSDoc comments as reStructuredText
* **Multiple Directives**: Support for classes, interfaces, and data
* **Tree-sitter Parsing**: Robust TypeScript parsing
* **Sphinx Integration**: Full cross-referencing and indexing support
* **Type Information**: Display TypeScript type annotations and signatures

Example Output
--------------

Here's what the generated documentation looks like:

Calculator Class
~~~~~~~~~~~~~~~~

.. ts:autoclass:: Calculator
   :members:

Calculator Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. ts:autointerface:: CalculatorConfig
   :members:

Constants
~~~~~~~~~

.. ts:autodata:: DEFAULT_CONFIG

.. ts:autodata:: MATH_CONSTANTS

Utility Functions
~~~~~~~~~~~~~~~~~

.. ts:autodata:: isSafeInteger

.. ts:autodata:: formatNumber

Error Classes
~~~~~~~~~~~~~

.. ts:autoclass:: CalculationError

Cross-References
----------------

The extension provides several roles for cross-referencing TypeScript objects:

* :ts:class:`Calculator` - Reference to a class
* :ts:interface:`CalculatorConfig` - Reference to an interface
* :ts:meth:`Calculator.add` - Reference to a method
* :ts:prop:`Calculator.memory` - Reference to a property
* :ts:func:`isSafeInteger` - Reference to a function
* :ts:var:`DEFAULT_CONFIG` - Reference to a variable

Configuration Options
---------------------

The extension supports several configuration options in your ``conf.py``:

.. code-block:: python

   # Directories to scan for TypeScript files
   sphinx_ts_src_dirs = ['src', 'lib', 'types']

   # Files to exclude from parsing
   sphinx_ts_exclude_patterns = [
       '**/*.test.ts',
       '**/*.spec.ts',
       '**/node_modules/**'
   ]

   # Include private members
   sphinx_ts_include_private = False

   # Include inherited members
   sphinx_ts_include_inherited = True

Supported JSDoc Tags
--------------------

The extension recognizes and renders the following JSDoc tags:

* ``@param {type} name description`` - Parameter documentation
* ``@returns description`` - Return value documentation
* ``@example`` - Code examples
* ``@since version`` - Version information
* ``@deprecated message`` - Deprecation notices
* Custom tags are also preserved

Getting Help
------------

If you encounter issues or have questions:

* Check the :doc:`usage` guide for detailed instructions
* Look at the :doc:`examples` for common patterns
* Visit our GitHub repository for bug reports and feature requests

License
-------

This project is licensed under the MIT License.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
