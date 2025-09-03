"""TypeScript Data Auto-Directive Module.

Contains the TSAutoDataDirective class for auto-documenting TypeScript
variables, constants, and functions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging

from .base import TSAutoDirective

if TYPE_CHECKING:
    from sphinx_ts.parser import TSValueParser, TSVariable

logger = logging.getLogger(__name__)


class TSAutoDataDirective(TSAutoDirective):
    """Auto-documentation directive for TypeScript variables/constants."""

    def run(self) -> list[nodes.Node]:
        """Run the variable auto-documentation directive."""
        variable_name = self.arguments[0]

        # Find and register the variable using common processing pattern
        result = self._process_object_common(variable_name, "variable")

        # If not found as a variable, try to find it as a function
        if not result:
            function_result = self._process_object_common(
                variable_name, "function"
            )
            if function_result:
                return self._process_function(function_result, variable_name)
            return []

        ts_variable: TSVariable = result["object"]

        # Create the main variable directive
        var_node = nodes.section(ids=[f"variable-{variable_name}"])

        # Create variable signature for the title - only include name and type
        signature = variable_name
        if ts_variable.type_annotation:
            formatted_type = self.format_parameter_type(
                ts_variable.type_annotation, add_colon=True
            )
            signature += f" {formatted_type}"

        # Add variable title
        title = nodes.title(text=signature)
        var_node.append(title)

        # Add variable kind (const, let, var) as a subtitle
        kind_para = nodes.paragraph(classes=["ts-variable-kind"])
        kind_para.append(nodes.emphasis(text=f"{ts_variable.kind}"))
        var_node.append(kind_para)

        # Add variable documentation (description for the whole variable)
        # But exclude @param tags which will be shown in the value table
        doc_lines = []
        if ts_variable.doc_comment:
            # Extract only the description and non-param documentation
            if ts_variable.doc_comment.description:
                doc_lines.extend(
                    ts_variable.doc_comment.description.split("\n")
                )
                doc_lines.append("")

            # Skip returns in doc comment since we'll handle it separately
            # (We handle returns separately with format_returns_section)

            if ts_variable.doc_comment.examples:
                # Use rubric instead of section to exclude from TOC
                doc_lines.extend(
                    [".. rubric:: Examples", "   :class: ts-examples", ""]
                )
                # Use only one code block for all examples to prevent duplication
                doc_lines.append(".. code-block:: typescript")
                doc_lines.append("")
                for example in ts_variable.doc_comment.examples:
                    doc_lines.extend(
                        f"   {line}" for line in example.split("\n")
                    )
                    if example != ts_variable.doc_comment.examples[-1]:
                        doc_lines.append(
                            "   "
                        )  # Add separator between examples
                doc_lines.append("")

            if ts_variable.doc_comment.deprecated:
                doc_lines.extend(
                    [
                        ".. warning::",
                        "",
                        f"   **Deprecated**: {ts_variable.doc_comment.deprecated}",
                        "",
                    ]
                )

            if ts_variable.doc_comment.since:
                doc_lines.extend(
                    [
                        ".. note::",
                        "",
                        f"   Available since version {ts_variable.doc_comment.since}",
                        "",
                    ]
                )

        if doc_lines:
            var_node.extend(self.create_rst_content(doc_lines))

        # Add returns section using the shared method
        if ts_variable.doc_comment and ts_variable.doc_comment.returns:
            self.format_returns_section(var_node, ts_variable.doc_comment)

        # Source file information removed for cleaner TOC

        # Add value if available
        if ts_variable.value:
            # Use rubric for value instead of section to exclude from TOC
            value_container = nodes.container(classes=["ts-value-container"])
            value_rubric = nodes.rubric(text="Value")
            value_rubric["classes"] = ["ts-value"]
            value_container.append(value_rubric)

            # Parse the value to determine how to display it
            # TSValueParser already imported at top

            value_data = TSValueParser.parse_value(ts_variable.value)

            # For const values (which are likely to have complex properties), use a code block
            if ts_variable.kind == "const" and (
                value_data["type"] == "object"
                or value_data["type"].endswith("[]")
                or "{" in ts_variable.value
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
                value_container.append(code_block)

                # Add property descriptions after the code block if available
                if ts_variable.doc_comment and ts_variable.doc_comment.params:
                    # Use rubric for property descriptions to exclude from TOC
                    props_rubric = nodes.rubric(text="Property Descriptions")
                    props_rubric["classes"] = ["ts-property-descriptions"]
                    value_container.append(props_rubric)

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
                        value_container.append(prop_list)
            else:
                # Use table for simpler values
                value_table = self._create_value_table(ts_variable)
                if value_table:
                    value_container.append(value_table)
                else:
                    # Fallback to simple display if table creation fails
                    value_para = nodes.paragraph()
                    value_code = nodes.literal(text=ts_variable.value)
                    value_para += value_code
                    value_container.append(value_para)

            var_node.append(value_container)

        return [var_node]

    def _create_value_table(
        self, ts_variable: TSVariable
    ) -> nodes.table | None:
        """Create a table showing the variable value with type info and descriptions."""
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
        field_docs = {}
        if ts_variable.doc_comment and ts_variable.doc_comment.params:
            field_docs = ts_variable.doc_comment.params

        # If value is None, return None
        if ts_variable.value is None:
            return None

        # Use the TSValueParser to parse the value
        # TSValueParser already imported at top

        value_data = TSValueParser.parse_value(ts_variable.value)

        # Check if it's a const with a complex value - we'll use a code block instead
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
        self, result: dict[str, Any], function_name: str
    ) -> list[nodes.Node]:
        """Process a TypeScript function and render it as data."""
        ts_function = result["object"]

        # Note: function is already registered via _process_object_common call

        func_node = addnodes.desc(
            domain="ts",
            objtype="function",
            noindex=False,
        )
        func_node["ids"] = [f"function-{function_name}"]

        # Create function signature
        sig = addnodes.desc_signature("", "", first=True)
        sig["class"] = "sig-object ts"
        sig["ids"] = [f"function-{function_name}"]
        func_node += sig

        # Add function name
        sig += addnodes.desc_name("", function_name)

        # Add parameter list
        paramlist = addnodes.desc_parameterlist()
        sig += paramlist

        # Add parameters to signature
        if ts_function.parameters:
            for param in ts_function.parameters:
                parameter = addnodes.desc_parameter("", "")
                paramlist += parameter

                # Use the shared parameter formatting helper
                self.format_parameter_nodes(parameter, param)

        # Add return type
        if ts_function.return_type:
            sig += nodes.Text(": ")
            formatted_type = self.format_parameter_type(ts_function.return_type)
            sig += addnodes.desc_type("", formatted_type)

        # Add content container
        content = addnodes.desc_content()
        func_node += content

        # Add function documentation
        if ts_function.doc_comment and ts_function.doc_comment.description:
            desc_para = nodes.paragraph()
            desc_para.append(nodes.Text(ts_function.doc_comment.description))
            content.append(desc_para)

        # Add parameter information
        if ts_function.parameters:
            # Extract documented parameters from doc_comment if it exists
            documented_params = {}
            if ts_function.doc_comment and ts_function.doc_comment.params:
                documented_params = ts_function.doc_comment.params

            # Add a rubric for parameters
            param_rubric = nodes.rubric(text="Parameters")
            content.append(param_rubric)

            # Create field list for parameters
            field_list = nodes.field_list()
            content.append(field_list)

            # Add parameters as field items
            for param in ts_function.parameters:
                # Create field item
                field = nodes.field()
                field_list.append(field)

                # Create field name with parameter name and optional marker
                field_name = nodes.field_name("")
                self.format_optional_parameter(
                    field_name,
                    param["name"],
                    param.get("optional", False),
                    in_signature=False,
                )

                field.append(field_name)

                # Create field body with type and description
                field_body = nodes.field_body()
                field.append(field_body)

                # Create paragraph for type information
                type_para = nodes.paragraph()
                if param.get("type"):
                    type_para.append(nodes.strong("Type: "))
                    formatted_type = self.format_parameter_type(
                        param.get("type")
                    )
                    type_para.append(nodes.literal("", formatted_type))
                    if param.get("default"):
                        type_para.append(
                            nodes.Text(f", default: {param.get('default')}")
                        )
                    field_body.append(type_para)

                # Create paragraph for description
                if param["name"] in documented_params:
                    desc_para = nodes.paragraph()
                    desc_para.append(
                        nodes.Text(documented_params[param["name"]])
                    )
                    field_body.append(desc_para)

        # Add returns documentation using the shared method
        if ts_function.doc_comment and ts_function.doc_comment.returns:
            self.format_returns_section(
                content, ts_function.doc_comment, ts_function.return_type
            )

        # Add examples documentation
        self._add_examples_section(content, ts_function.doc_comment)

        return [func_node]
