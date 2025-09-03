/**
 * Example TypeScript file demonstrating various enum patterns
 * for testing the ts:autoenum directive.
 */

/**
 * Basic string enum for HTTP status categories.
 *
 * @example
 * ```typescript
 * const status = HttpStatusCategory.SUCCESS;
 * console.log(status); // "success"
 * ```
 */
export enum HttpStatusCategory {
  /** Informational responses (100-199) */
  INFORMATIONAL = "informational",
  /** Successful responses (200-299) */
  SUCCESS = "success",
  /** Redirection messages (300-399) */
  REDIRECTION = "redirection",
  /** Client error responses (400-499) */
  CLIENT_ERROR = "client_error",
  /** Server error responses (500-599) */
  SERVER_ERROR = "server_error",
}

/**
 * Numeric enum for log levels with explicit values.
 *
 * @since 1.2.0
 * @example
 * ```typescript
 * if (level >= LogLevel.WARN) {
 *   console.warn("Warning or error occurred");
 * }
 * ```
 */
export enum LogLevel {
  /** Debug level logging */
  DEBUG = 0,
  /** Informational messages */
  INFO = 1,
  /** Warning messages */
  WARN = 2,
  /** Error messages */
  ERROR = 3,
  /** Fatal error messages */
  FATAL = 4,
}

/**
 * Auto-incremented numeric enum for user roles.
 * Values start at 0 and increment automatically.
 */
export enum UserRole {
  /** Guest user with no special permissions */
  GUEST,
  /** Regular user with basic permissions */
  USER,
  /** Moderator with elevated permissions */
  MODERATOR,
  /** Administrator with full permissions */
  ADMIN,
}

/**
 * Mixed enum with both string and computed values.
 *
 * @deprecated Use Theme enum instead
 */
export enum Color {
  /** Primary brand color */
  PRIMARY = "#007bff",
  /** Secondary brand color */
  SECONDARY = "#6c757d",
  /** Success indicator color */
  SUCCESS = "#28a745",
  /** Warning indicator color */
  WARNING = "#ffc107",
  /** Danger/error indicator color */
  DANGER = "#dc3545",
  /** Computed white color */
  WHITE = "#ffffff",
  /** Computed black color */
  BLACK = "#000000",
}

/**
 * Const enum for better performance and tree-shaking.
 * Values are inlined at compile time.
 */
export const enum Direction {
  /** North direction */
  NORTH = "north",
  /** South direction */
  SOUTH = "south",
  /** East direction */
  EAST = "east",
  /** West direction */
  WEST = "west",
}

/**
 * Bit flag enum for permissions system.
 * Each permission is a power of 2 for bitwise operations.
 *
 * @example
 * ```typescript
 * const userPerms = Permission.READ | Permission.WRITE;
 * const canDelete = (userPerms & Permission.DELETE) !== 0;
 * ```
 */
export enum Permission {
  /** No permissions */
  NONE = 0,
  /** Read permission */
  READ = 1 << 0,  // 1
  /** Write permission */
  WRITE = 1 << 1, // 2
  /** Execute permission */
  EXECUTE = 1 << 2, // 4
  /** Delete permission */
  DELETE = 1 << 3, // 8
  /** Admin permission (all permissions) */
  ADMIN = READ | WRITE | EXECUTE | DELETE,
}

/**
 * Reverse mapping enum for status codes.
 * Demonstrates both numeric keys and string values.
 */
export enum StatusCode {
  /** OK status */
  OK = 200,
  /** Created status */
  CREATED = 201,
  /** Bad Request */
  BAD_REQUEST = 400,
  /** Unauthorized */
  UNAUTHORIZED = 401,
  /** Forbidden */
  FORBIDDEN = 403,
  /** Not Found */
  NOT_FOUND = 404,
  /** Internal Server Error */
  INTERNAL_SERVER_ERROR = 500,
}

/**
 * Ambient enum declaration (typically from declaration files).
 * These are used when the enum is defined elsewhere.
 */
declare enum ExternalEnum {
  /** First external value */
  FIRST,
  /** Second external value */
  SECOND,
}

/**
 * Helper function to get all enum values.
 *
 * @param enumObject The enum to get values from
 * @returns Array of enum values
 */
export function getEnumValues<T>(enumObject: Record<string, T>): T[] {
  return Object.values(enumObject);
}

/**
 * Helper function to check if a value is a valid enum member.
 *
 * @param enumObject The enum to check against
 * @param value The value to check
 * @returns True if the value is a valid enum member
 */
export function isValidEnumValue<T>(
  enumObject: Record<string, T>,
  value: unknown
): value is T {
  return Object.values(enumObject).includes(value as T);
}

/**
 * Type alias for theme colors.
 */
export type ThemeColor = keyof typeof Color;

/**
 * Configuration object using enum values.
 */
export const DEFAULT_CONFIG = {
  logLevel: LogLevel.INFO,
  theme: Color.PRIMARY,
  permissions: Permission.READ | Permission.WRITE,
  statusCategory: HttpStatusCategory.SUCCESS,
} as const;
