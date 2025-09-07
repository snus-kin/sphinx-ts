"""TypeScript Data Auto-Directive Module.

Contains the TSAutoDataDirective class for auto-documenting TypeScript
variables, constants, and functions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging as sphinx_logging

from sphinx_ts.parser import TSValueParser

from .base import TSAutoDirective

if TYPE_CHECKING:
    from sphinx_ts.parser import TSVariable

logger = sphinx_logging.getLogger(__name__)


class TSAutoDataDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript variables/constants."""

    def run(self) -> list[nodes.Node]:
        """Run the variable auto-documentation directive."""
        variable_name = self.arguments[0]

        # Find and register the variable using common processing pattern
        # Use debug level for initial variable lookup since we have fallbacks
        result = self._process_object_common(
            variable_name, "variable", log_level=logging.DEBUG
        )
        if result:
            logger.debug("Found '%s' as variable", variable_name)
        else:
            logger.debug(
                "Variable '%s' not found, trying as function", variable_name
            )

        # If not found as a variable, try to find it as a function
        if not result:
            function_result = self._process_object_common(
                variable_name, "function"
            )
            if function_result:
                logger.debug("Found '%s' as function", variable_name)
                return self._process_function(function_result, variable_name)

            logger.debug(
                "Function '%s' not found, trying as type alias", variable_name
            )
            # If not found as a function, try to find it as a type alias
            type_result = self._process_object_common(variable_name, "type")
            if type_result:
                logger.debug("Found '%s' as type alias", variable_name)
                return self._process_type_alias(type_result, variable_name)

            logger.warning(
                "Could not find TypeScript object '%s' as variable, function, "
                "or type",
                variable_name,
            )
            return []

        ts_variable: TSVariable = result["object"]

        # Create standardized variable descriptor
        var_node, var_sig, var_content = self._create_standard_desc_node(
            "variable", variable_name
        )

        # Create variable signature with type annotation
        modifiers = [ts_variable.kind] if hasattr(ts_variable, "kind") else []
        self._create_standard_signature(
            var_sig, variable_name, modifiers=modifiers
        )

        # Add type annotation if present
        if ts_variable.type_annotation:
            formatted_type = self.format_parameter_type(
                ts_variable.type_annotation, add_colon=True
            )
            var_sig += nodes.Text(formatted_type)

        # Add standardized documentation content (skip params for now, handle
        # separately)
        self._add_standard_doc_content(
            var_content, ts_variable.doc_comment, skip_params=True
        )

        # Add value information if available
        if ts_variable.value:
            # Create a value section within the content
            value_title = nodes.paragraph()
            value_title += nodes.strong(text="Value:")
            var_content.append(value_title)

            # Parse the value to determine how to display it
            value_data = TSValueParser.parse_value(ts_variable.value)

            # For const values with complex properties, use a code block
            if (
                hasattr(ts_variable, "kind")
                and ts_variable.kind == "const"
                and (
                    value_data["type"] == "object"
                    or value_data["type"].endswith("[]")
                    or "{" in ts_variable.value
                )
            ):
                # Add a prefix to show this is a constant declaration
                declaration = f"const {ts_variable.name} = "

                # Format the value with proper syntax highlighting
                formatted_value = TSValueParser.format_value(ts_variable.value)

                # Combine the declaration and value
                full_code = f"{declaration}{formatted_value};"

                code_block = nodes.literal_block(text=full_code)
                code_block["language"] = "typescript"
                code_block["classes"] = ["highlight"]
                var_content.append(code_block)

                # Add property descriptions after the code block if available
                if ts_variable.doc_comment and ts_variable.doc_comment.params:
                    props_title = nodes.paragraph()
                    props_title += nodes.strong(text="Property Descriptions:")
                    var_content.append(props_title)

                    # Create a definition list for properties
                    prop_list = nodes.definition_list()
                    prop_list["classes"] = ["ts-property-descriptions"]

                    # Sort properties alphabetically for easier reference
                    sorted_props = sorted(
                        ts_variable.doc_comment.params.items()
                    )

                    for prop_name, prop_desc in sorted_props:
                        if prop_desc:
                            term_item = nodes.term()
                            term_item += nodes.literal(text=prop_name)

                            def_item = nodes.definition()
                            def_item += nodes.paragraph(text=prop_desc)

                            list_item = nodes.definition_list_item()
                            list_item += term_item
                            list_item += def_item
                            prop_list += list_item

                    if len(prop_list.children) > 0:
                        var_content.append(prop_list)
            else:
                # Use table for simpler values
                value_table = self._create_value_table(ts_variable)
                if value_table:
                    var_content.append(value_table)
                else:
                    # Fallback to simple display if table creation fails
                    value_para = nodes.paragraph()
                    value_code = nodes.literal(text=ts_variable.value)
                    value_para += value_code
                    var_content.append(value_para)

        return [var_node]

    def _create_value_table(
        self, ts_variable: TSVariable
    ) -> nodes.table | None:
        """Create a table showing the variable value with type info."""
        # Create a table for the value
        table = nodes.table(classes=["variable-value-table"])
        tgroup = nodes.tgroup(cols=4)
        table += tgroup

        # Add column specs - name/field, type, value, description
        tgroup.append(nodes.colspec(colwidth=15))
        tgroup.append(nodes.colspec(colwidth=15))
        tgroup.append(nodes.colspec(colwidth=25))
        tgroup.append(nodes.colspec(colwidth=45))

        # Create table header
        thead = nodes.thead()
        tgroup += thead
        header_row = nodes.row()
        header_row.append(nodes.entry("", nodes.paragraph(text="Field")))
        header_row.append(nodes.entry("", nodes.paragraph(text="Type")))
        header_row.append(nodes.entry("", nodes.paragraph(text="Value")))
        header_row.append(nodes.entry("", nodes.paragraph(text="Description")))
        thead.append(header_row)

        # Create table body
        tbody = nodes.tbody()
        tgroup += tbody

        # Get documentation for fields from JSDoc comments
        if ts_variable.doc_comment and ts_variable.doc_comment.params:
            pass  # field_docs would be assigned here but not currently used

        # If value is None, return None
        if ts_variable.value is None:
            return None

        # Use the TSValueParser to parse the value
        # TSValueParser already imported at top

        value_data = TSValueParser.parse_value(ts_variable.value)

        # Check if it's a const with a complex value - use a code block
        if ts_variable.kind == "const" and (
            (value_data["type"] == "object" and value_data["properties"])
            or value_data["type"].endswith("[]")
            or "{" in ts_variable.value
        ):
            return None

        # For simple values, create a single row
        value_row = nodes.row()

        # Value name cell
        name_cell = nodes.entry()
        name_cell += nodes.paragraph(text="(value)")
        value_row.append(name_cell)

        # Value type cell
        type_cell = nodes.entry()
        if ts_variable.type_annotation:
            type_para = nodes.paragraph()
            type_para += nodes.literal(
                text=self.format_type_annotation(ts_variable.type_annotation)
            )
            type_cell += type_para
        elif value_data["type"] != "unknown":
            type_para = nodes.paragraph()
            type_para += nodes.literal(text=value_data["type"])
            type_cell += type_para
        value_row.append(type_cell)

        # Value content cell - the actual value
        content_cell = nodes.entry()
        value_text = ts_variable.value if ts_variable.value is not None else ""

        # Format the value appropriately
        if value_data["type"] in ["object", "array"]:
            # Format complex values with syntax highlighting
            # TSValueParser already imported at top

            formatted_value = TSValueParser.format_value(value_text)
            code_block = nodes.literal_block(text=formatted_value)
            code_block["language"] = "typescript"
            code_block["classes"] = ["highlight"]
            content_cell += code_block
        else:
            content_para = nodes.paragraph()
            content_para += nodes.literal(text=value_text)
            content_cell += content_para

        value_row.append(content_cell)

        # Value description cell
        desc_cell = nodes.entry()
        if ts_variable.doc_comment and ts_variable.doc_comment.description:
            desc_para = nodes.paragraph()
            desc_text = str(ts_variable.doc_comment.description or "")
            desc_para += nodes.Text(desc_text)
            desc_cell += desc_para
        value_row.append(desc_cell)

        tbody.append(value_row)

        return table

    def _process_function(
        self, result: dict, function_name: str
    ) -> list[nodes.Node]:
        """Process a TypeScript function."""
        ts_function = result["object"]

        # Create standardized function descriptor
        func_node, func_sig, func_content = self._create_standard_desc_node(
            "function", function_name
        )

        # Create function signature with parameters and explicit CSS class for
        # red styling
        func_name_node = addnodes.desc_sig_name(function_name, function_name)
        func_name_node["classes"] = ["sig-name", "descname"]
        func_sig += func_name_node

        # Add parameter list
        paramlist = addnodes.desc_parameterlist()
        func_sig += paramlist

        # Add parameters to signature
        if ts_function.parameters:
            for param in ts_function.parameters:
                parameter = addnodes.desc_parameter("", "")
                paramlist += parameter

                # Use the shared parameter formatting helper
                self.format_parameter_nodes(parameter, param)

        # Add return type
        if ts_function.return_type:
            func_sig += nodes.Text(": ")
            formatted_type = self.format_parameter_type(ts_function.return_type)
            func_sig += nodes.emphasis("", formatted_type)

        # Add standardized documentation content
        self._add_standard_doc_content(func_content, ts_function.doc_comment)

        # Add parameter information using shared method
        if ts_function.parameters:
            self._add_parameter_list(func_content, ts_function)

        # Add returns documentation
        if ts_function.doc_comment and ts_function.doc_comment.returns:
            self._add_method_returns(func_content, ts_function)

        # Add examples documentation
        if ts_function.doc_comment:
            self._add_examples_section(func_content, ts_function.doc_comment)

        return [func_node]

    def _process_type_alias(
        self, result: dict, type_alias_name: str
    ) -> list[nodes.Node]:
        """Process a TypeScript type alias."""
        type_alias = result["object"]

        # Create standardized type alias descriptor
        type_node, type_sig, type_content = self._create_standard_desc_node(
            "type", type_alias_name
        )

        # Create type alias signature
        self._create_standard_signature(
            type_sig,
            type_alias_name,
            "type",
            type_params=type_alias.get("type_parameters"),
        )

        # Add type definition
        type_def = type_alias.get("type_definition", "")
        if type_def:
            formatted_type_def = self.format_type_annotation(type_def)
            type_sig += nodes.Text(f" = {formatted_type_def}")

        # Add standardized documentation content
        doc_comment = type_alias.get("doc_comment")
        self._add_standard_doc_content(type_content, doc_comment)

        return [type_node]
