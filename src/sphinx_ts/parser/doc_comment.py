"""TypeScript JSDoc Comment Parser.

Contains the TSDocComment class for parsing and representing JSDoc comments
found in TypeScript code.
"""

from __future__ import annotations

import re


class TSDocComment:
    """Represents a TypeScript JSDoc comment."""

    def __init__(self, text: str) -> None:
        """Initialize a TypeScript JSDoc comment.

        Args:
            text: The raw JSDoc comment text

        """
        self.text = text
        self.description = ""
        self.params: dict[str, str] = {}
        self.returns: str | None = None
        self.examples: list[str] = []
        self.deprecated: str | None = None
        self.since: str | None = None
        self.tags: dict[str, str] = {}

        self._parse()

    def _parse(self) -> None:
        """Parse JSDoc comment text."""
        # Remove comment markers
        lines = []
        for original_line in self.text.split("\n"):
            processed_line = original_line.strip()
            if processed_line.startswith("/**"):
                processed_line = processed_line[3:].strip()
                # Handle case where */ is on the same line as /**
                if processed_line.endswith("*/"):
                    processed_line = processed_line[:-2].strip()
            elif processed_line.startswith("*/"):
                continue
            elif processed_line.startswith("*"):
                processed_line = processed_line[1:].strip()
                # Handle case where */ is at the end of a line starting with *
                if processed_line.endswith("*/"):
                    processed_line = processed_line[:-2].strip()

            # Also handle case where */ appears at end of any line
            if processed_line.endswith("*/"):
                processed_line = processed_line[:-2].strip()

            lines.append(processed_line)

        content = "\n".join(lines).strip()

        # Split into description and tags
        parts = re.split(r"\n\s*@", content, maxsplit=1)
        self.description = parts[0].strip()

        if len(parts) > 1:
            tag_content = parts[1]
            self._parse_tags("@" + tag_content)

    def _parse_tags(self, tag_content: str) -> None:
        """Parse JSDoc tags."""
        tags = re.findall(
            r"@(\w+)(?:\s+([^@]+))?",
            tag_content,
            re.MULTILINE | re.DOTALL,
        )

        # Clear examples list before parsing to avoid duplicates
        self.examples = []

        for tag_name, original_tag_value in tags:
            tag_value = original_tag_value.strip() if original_tag_value else ""

            if tag_name == "param":
                # Parse @param {type} name description
                match = re.match(
                    r"(?:\{([^}]+)\})?\s*(\w+)(?:\s+(.+))?",
                    tag_value,
                    re.DOTALL,
                )
                if match:
                    param_type, param_name, param_desc = match.groups()
                    self.params[param_name] = param_desc or ""
            elif tag_name in {"returns", "return"}:
                self.returns = tag_value
            elif tag_name == "example":
                # Process markdown code blocks more carefully
                tag_value = re.sub(r"```typescript\s*", "", tag_value)
                tag_value = re.sub(r"```\s*$", "", tag_value)
                tag_value = tag_value.strip()
                if tag_value:  # Only add non-empty examples
                    self.examples.append(tag_value)
            elif tag_name == "deprecated":
                self.deprecated = tag_value
            elif tag_name == "since":
                self.since = tag_value
            else:
                self.tags[tag_name] = tag_value
