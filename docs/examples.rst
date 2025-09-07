Examples
========

This page shows actual examples of generated documentation using the TypeScript Sphinx Extension with our example TypeScript file.

Calculator Class Example
------------------------

The following documentation is automatically generated from the ``examples/calculator.ts`` file:

.. ts:autoclass:: Calculator
   :members:
   :undoc-members:

Calculator Configuration
------------------------

The configuration interface used by the Calculator:

.. ts:autointerface:: CalculatorConfig
   :members:
   :undoc-members:

Operation Interface
-------------------

Interface defining calculator operations:

.. ts:autointerface:: Operation
   :members:

Constants and Variables
-----------------------

Default Configuration
~~~~~~~~~~~~~~~~~~~~~

.. ts:autodata:: DEFAULT_CONFIG

Mathematical Constants
~~~~~~~~~~~~~~~~~~~~~~

.. ts:autodata:: MATH_CONSTANTS

Utility Functions
-----------------

Safe Integer Check
~~~~~~~~~~~~~~~~~~

.. ts:autodata:: isSafeInteger

Number Formatting
~~~~~~~~~~~~~~~~~

.. ts:autodata:: formatNumber

Error Classes
-------------

Calculation Error
~~~~~~~~~~~~~~~~~

.. ts:autoclass:: CalculationError

Cross-Reference Examples
------------------------

Here are examples of cross-referencing TypeScript objects:

Class References
~~~~~~~~~~~~~~~~

You can reference the main :ts:class:`Calculator` class, or the error class :ts:class:`CalculationError`.

Interface References
~~~~~~~~~~~~~~~~~~~~

Reference interfaces like :ts:interface:`CalculatorConfig` or :ts:interface:`Operation`.

Method References
~~~~~~~~~~~~~~~~~

Reference specific methods:

- :ts:meth:`Calculator.add` - Addition method
- :ts:meth:`Calculator.subtract` - Subtraction method
- :ts:meth:`Calculator.multiply` - Multiplication method
- :ts:meth:`Calculator.divide` - Division method
- :ts:meth:`Calculator.power` - Exponentiation method
- :ts:meth:`Calculator.sqrt` - Square root method
- :ts:meth:`Calculator.chain` - Chain operations method

Property References
~~~~~~~~~~~~~~~~~~~

Reference properties like :ts:meth:`Calculator.memory`.

Enum Member References
~~~~~~~~~~~~~~~~~~~~~~

Reference specific enum members:

- :ts:enum_member:`HttpStatusCategory.SUCCESS` - Successful responses
- :ts:enum_member:`LogLevel.ERROR` - Error level logging
- :ts:enum_member:`Permission.READ` - Read permission flag
- :ts:enum_member:`UserRole.ADMIN` - Administrator role

Function and Variable References
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reference utility functions and constants:

- :ts:func:`isSafeInteger` - Check if number is safe
- :ts:func:`formatNumber` - Format number for display
- :ts:var:`DEFAULT_CONFIG` - Default configuration
- :ts:var:`MATH_CONSTANTS` - Mathematical constants

Generic References
~~~~~~~~~~~~~~~~~~

You can also use the generic :ts:obj:`Calculator` reference when you're not sure of the object type.

Usage Examples
--------------

Basic Calculator Usage
~~~~~~~~~~~~~~~~~~~~~~

Here's how to use the :ts:class:`Calculator` with the :ts:var:`DEFAULT_CONFIG`:

.. code-block:: typescript

   import { Calculator, DEFAULT_CONFIG } from './calculator';

   // Create calculator with default config
   const calc = new Calculator(DEFAULT_CONFIG);

   // Basic arithmetic
   const sum = calc.add(10, 5);         // 15
   const difference = calc.subtract(10, 5); // 5
   const product = calc.multiply(10, 5);     // 50
   const quotient = calc.divide(10, 5);      // 2

   // Advanced operations
   const power = calc.power(2, 3);      // 8
   const root = calc.sqrt(16);          // 4

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

You can customize the calculator behavior using :ts:interface:`CalculatorConfig`:

.. code-block:: typescript

   const customConfig: CalculatorConfig = {
       precision: 4,
       roundResults: false,
       maxChainLength: 50
   };

   const calc = new Calculator(customConfig);

Chain Operations
~~~~~~~~~~~~~~~~

Use the :ts:meth:`Calculator.chain` method for complex calculations:

.. code-block:: typescript

   const operations: Operation[] = [
       { operation: 'add', operands: [10] },
       { operation: 'multiply', operands: [2] },
       { operation: 'subtract', operands: [5] }
   ];

   const result = calc.chain(operations); // ((0 + 10) * 2) - 5 = 15

Error Handling
~~~~~~~~~~~~~~

The calculator throws :ts:class:`CalculationError` for invalid operations:

.. code-block:: typescript

   try {
       calc.divide(10, 0); // Throws CalculationError
   } catch (error) {
       if (error instanceof CalculationError) {
           console.log(`Error code: ${error.code}`);
           console.log(`Error message: ${error.message}`);
       }
   }

Working with Constants
~~~~~~~~~~~~~~~~~~~~~~

Use the predefined mathematical constants from :ts:var:`MATH_CONSTANTS`:

.. code-block:: typescript

   import { MATH_CONSTANTS } from './calculator';

   const circumference = 2 * MATH_CONSTANTS.PI * radius;
   const area = MATH_CONSTANTS.PI * Math.pow(radius, 2);
   const diagonal = side * MATH_CONSTANTS.SQRT2;

Utility Functions
~~~~~~~~~~~~~~~~~

Use the utility functions for validation and formatting:

.. code-block:: typescript

   import { isSafeInteger, formatNumber } from './calculator';

   const value = 123.456789;

   if (isSafeInteger(value)) {
       console.log('Safe to use as integer');
   }

   const formatted = formatNumber(value, 2); // "123.46"
   console.log(`Formatted: ${formatted}`);

Generated Documentation Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The generated documentation includes:

Type Information
~~~~~~~~~~~~~~~~

- Parameter types and default values
- Return types
- Property types
- Generic type parameters
- Union and intersection types

JSDoc Integration
~~~~~~~~~~~~~~~~~

- Full JSDoc comment parsing
- Parameter descriptions
- Return value documentation
- Code examples
- Version information
- Deprecation notices

Cross-References
~~~~~~~~~~~~~~~~

- Automatic linking between related types
- Method and property references
- Inheritance information
- Interface implementations

Source Information
~~~~~~~~~~~~~~~~~~

- Source file references
- Line number information (when available)
- Module exports

This example demonstrates the power of the TypeScript Sphinx Extension to automatically generate comprehensive documentation from well-commented TypeScript source code.

Enums Documentation
===================

This section demonstrates the enum auto-documentation capabilities.

HTTP Status Categories
----------------------

.. ts:autoenum:: HttpStatusCategory

Log Levels
----------

.. ts:autoenum:: LogLevel

User Roles
----------

.. ts:autoenum:: UserRole

Colors
------

.. ts:autoenum:: Color

Directions (Const Enum)
-----------------------

.. ts:autoenum:: Direction

Permissions (Bit Flags)
-----------------------

.. ts:autoenum:: Permission

Status Codes
------------

.. ts:autoenum:: StatusCode

External Enum (Declare)
-----------------------

.. ts:autoenum:: ExternalEnum

Cross-References
================

You can reference TypeScript objects using the provided roles:

- Classes: :ts:class:`Calculator`
- Interfaces: :ts:interface:`CalculatorConfig`
- Enums: :ts:enum:`HttpStatusCategory`
- Methods: :ts:meth:`Calculator.add`
- Properties: :ts:prop:`Calculator.memory`
- Functions: :ts:func:`isSafeInteger`
- Variables: :ts:var:`DEFAULT_CONFIG`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
