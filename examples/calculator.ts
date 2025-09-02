/**
 * A comprehensive calculator class demonstrating various TypeScript features
 * and JSDoc documentation patterns for the ts-sphinx extension.
 *
 * This class provides basic arithmetic operations and serves as an example
 * of how the TypeScript Sphinx extension handles different code patterns.
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
   * This value persists between operations.
   */
  private _memory: number = 0;

  /**
   * Configuration options for the calculator.
   */
  private _config: CalculatorConfig;

  /**
   * Static constant for the maximum safe integer value.
   */
  public static readonly MAX_SAFE_VALUE = Number.MAX_SAFE_INTEGER;

  /**
   * Creates a new Calculator instance.
   *
   * @param config Optional configuration for the calculator
   * @example
   * ```typescript
   * const calc = new Calculator({ precision: 4 });
   * ```
   */
  constructor(config?: CalculatorConfig) {
    this._config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Gets the current memory value.
   *
   * @returns The current value in memory
   */
  get memory(): number {
    return this._memory;
  }

  /**
   * Sets the memory value.
   *
   * @param value The value to store in memory
   */
  set memory(value: number) {
    this._memory = this.roundIfNeeded(value);
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
    const result = a + b;
    return this.roundIfNeeded(result);
  }

  /**
   * Subtracts the second number from the first.
   *
   * @param a The number to subtract from
   * @param b The number to subtract
   * @returns The difference of a and b
   */
  public subtract(a: number, b: number): number {
    const result = a - b;
    return this.roundIfNeeded(result);
  }

  /**
   * Multiplies two numbers together.
   *
   * @param a The first number to multiply
   * @param b The second number to multiply
   * @returns The product of a and b
   */
  public multiply(a: number, b: number): number {
    const result = a * b;
    return this.roundIfNeeded(result);
  }

  /**
   * Divides the first number by the second.
   *
   * @param a The dividend
   * @param b The divisor
   * @returns The quotient of a divided by b
   * @throws Error when dividing by zero
   * @example
   * ```typescript
   * const result = calc.divide(10, 2);
   * console.log(result); // 5
   * ```
   */
  public divide(a: number, b: number): number {
    if (b === 0) {
      throw new Error("Division by zero is not allowed");
    }
    const result = a / b;
    return this.roundIfNeeded(result);
  }

  /**
   * Raises a number to the power of another number.
   *
   * @param base The base number
   * @param exponent The exponent
   * @returns The result of base raised to the power of exponent
   */
  public power(base: number, exponent: number): number {
    const result = Math.pow(base, exponent);
    return this.roundIfNeeded(result);
  }

  /**
   * Calculates the square root of a number.
   *
   * @param value The number to find the square root of
   * @returns The square root of the input value
   * @throws Error for negative input values
   */
  public sqrt(value: number): number {
    if (value < 0) {
      throw new Error("Cannot calculate square root of negative number");
    }
    const result = Math.sqrt(value);
    return this.roundIfNeeded(result);
  }

  /**
   * Performs a series of operations in sequence.
   *
   * @param operations Array of operations to perform
   * @returns The final result after all operations
   * @example
   * ```typescript
   * const result = calc.chain([
   *   { operation: 'add', operands: [1, 2] },
   *   { operation: 'multiply', operands: [3] }
   * ]);
   * ```
   */
  public chain(operations: Operation[]): number {
    let result = 0;

    for (const op of operations) {
      switch (op.operation) {
        case "add":
          result = this.add(result, op.operands[0]);
          break;
        case "subtract":
          result = this.subtract(result, op.operands[0]);
          break;
        case "multiply":
          result = this.multiply(result, op.operands[0]);
          break;
        case "divide":
          result = this.divide(result, op.operands[0]);
          break;
        default:
          throw new Error(`Unknown operation: ${op.operation}`);
      }
    }

    return result;
  }

  /**
   * Rounds a number according to the calculator's precision settings.
   *
   * @param value The value to potentially round
   * @returns The rounded value if rounding is enabled, otherwise the original value
   * @private
   */
  private roundIfNeeded(value: number): number {
    if (this._config.roundResults) {
      const multiplier = Math.pow(10, this._config.precision);
      return Math.round(value * multiplier) / multiplier;
    }
    return value;
  }

  /**
   * Resets the calculator's memory to zero.
   */
  public clearMemory(): void {
    this._memory = 0;
  }

  /**
   * Gets the current configuration.
   *
   * @returns A copy of the current configuration
   */
  public getConfig(): CalculatorConfig {
    return { ...this._config };
  }

  /**
   * Updates the calculator configuration.
   *
   * @param config Partial configuration to merge with current settings
   */
  public updateConfig(config: Partial<CalculatorConfig>): void {
    this._config = { ...this._config, ...config };
  }
}

/**
 * Configuration interface for the Calculator class.
 * Defines various settings that affect calculator behavior.
 */
export interface CalculatorConfig {
  /**
   * Number of decimal places to round results to.
   * Must be a non-negative integer.
   *
   * @default 2
   */
  precision: number;

  /**
   * Whether to automatically round calculation results.
   * When false, results are returned with full precision.
   *
   * @default true
   */
  roundResults?: boolean;

  /**
   * Maximum number of operations to allow in a chain.
   * Helps prevent infinite loops or extremely long calculations.
   *
   * @default 100
   */
  maxChainLength?: number;
}

/**
 * Represents a single calculation operation.
 */
export interface Operation {
  /**
   * The type of operation to perform.
   */
  operation: "add" | "subtract" | "multiply" | "divide";

  /**
   * The operands for the operation.
   * Most operations require one operand (the other comes from the running result).
   */
  operands: number[];
}

/**
 * Type alias for supported operation types.
 */
export type OperationType = Operation["operation"];

/**
 * Default configuration values for new Calculator instances.
 *
 * @example
 * ```typescript
 * const calc = new Calculator(DEFAULT_CONFIG);
 * ```
 */
export const DEFAULT_CONFIG: CalculatorConfig = {
  precision: 2,
  roundResults: true,
  maxChainLength: 100,
};

/**
 * Mathematical constants commonly used in calculations.
 */
export const MATH_CONSTANTS = {
  /**
   * The mathematical constant π (pi).
   */
  PI: Math.PI,

  /**
   * The mathematical constant e (Euler's number).
   */
  E: Math.E,

  /**
   * The golden ratio (φ).
   */
  GOLDEN_RATIO: (1 + Math.sqrt(5)) / 2,

  /**
   * The square root of 2.
   */
  SQRT2: Math.SQRT2,
} as const;

/**
 * Utility function to check if a number is within the safe integer range.
 *
 * @param value The number to check
 * @returns True if the number is a safe integer, false otherwise
 */
export function isSafeInteger(value: number): boolean {
  return Number.isSafeInteger(value);
}

/**
 * Utility function to format numbers for display.
 *
 * @param value The number to format
 * @param precision Optional precision override
 * @returns Formatted string representation of the number
 */
export function formatNumber(value: number, precision?: number): string {
  if (precision !== undefined) {
    return value.toFixed(precision);
  }
  return value.toString();
}

/**
 * Error class for calculation-related errors.
 *
 * @example
 * ```typescript
 * throw new CalculationError("Invalid operation", "INVALID_OP");
 * ```
 */
export class CalculationError extends Error {
  /**
   * Error code for programmatic handling.
   */
  public readonly code: string;

  /**
   * Creates a new CalculationError.
   *
   * @param message Human-readable error message
   * @param code Machine-readable error code
   */
  constructor(message: string, code: string) {
    super(message);
    this.name = "CalculationError";
    this.code = code;
  }
}
