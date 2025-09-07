"""TypeScript Sphinx Domain.

Provides a Sphinx domain for TypeScript with roles and object types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast

from docutils import nodes
from docutils.nodes import Text, inline
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docfields import Field, TypedField
from sphinx.util.docutils import SphinxRole
from sphinx.util.nodes import make_refnode

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from docutils.nodes import Node, reference, system_message
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment

# Constants for object data tuple indices
OBJDATA_DOCNAME_INDEX = 0
OBJDATA_SYNOPSIS_INDEX = 1
OBJDATA_NOINDEX_INDEX = 2
OBJDATA_TUPLE_LENGTH = 3

logger = logging.getLogger(__name__)


def parse_parameters_from_signature(sig: str) -> list[dict[str, str]]:
    """Parse parameters from a TypeScript function signature.

    Args:
        sig: The function signature string

    Returns:
        List of parameter dictionaries with name, type, optional, default keys

    """
    parameters = []

    # Extract parameter list from signature
    if "(" not in sig:
        return parameters

    start = sig.index("(") + 1
    end = sig.rfind(")")
    if end == -1:
        return parameters

    param_str = sig[start:end].strip()
    if not param_str:
        return parameters

    # Simple parameter splitting - handles basic cases
    # This is a simplified parser that handles most common cases
    depth = 0
    current_param = ""

    for char in param_str:
        if char in "({[<":
            depth += 1
        elif char in ")}]>":
            depth -= 1
        elif char == "," and depth == 0:
            # End of parameter
            if current_param.strip():
                parameters.append(
                    _parse_single_parameter(current_param.strip())
                )
            current_param = ""
            continue

        current_param += char

    # Add the last parameter
    if current_param.strip():
        parameters.append(_parse_single_parameter(current_param.strip()))

    return parameters


def _parse_single_parameter(param: str) -> dict[str, str]:
    """Parse a single parameter string into components.

    Args:
        param: Single parameter string like "name: string" or "value?: number"

    Returns:
        Dictionary with name, type, optional, default keys

    """
    result = {"name": "", "type": "", "optional": "false", "default": ""}

    # Handle default values first
    if "=" in param:
        param, default = param.rsplit("=", 1)
        result["default"] = default.strip()
        param = param.strip()

    # Handle optional parameters
    if param.endswith("?"):
        result["optional"] = "true"
        param = param[:-1].strip()

    # Split name and type
    if ":" in param:
        name, type_part = param.split(":", 1)
        result["name"] = name.strip()
        type_str = type_part.strip()

        # Format union types properly (same logic as format_type_annotation)
        if "|" in type_str:
            # Clean up union type spacing
            union_parts = []
            parts = type_str.split("|")
            for part in parts:
                clean_part = " ".join(part.split())
                # Only add non-empty parts (handles leading | characters)
                if clean_part:
                    union_parts.append(clean_part)
            type_str = " | ".join(union_parts)
        else:
            # Normalize whitespace for non-union types
            type_str = " ".join(type_str.split())

        result["type"] = type_str
    else:
        result["name"] = param.strip()

    return result


class TypeScriptObject(ObjectDescription[str]):
    """Base class for TypeScript object descriptions."""

    option_spec: ClassVar[dict[str, Any]] = {
        "noindex": directives.flag,
        "module": directives.unchanged,
        "annotation": directives.unchanged,
    }

    def get_signature_prefix(self, _sig: str) -> str:
        """Return the prefix for the signature."""
        return ""

    def needs_arglist(self) -> bool:
        """Return True if this object needs an argument list."""
        return False

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Transform a signature into RST nodes."""
        return sig

    def add_target_and_index(
        self,
        name: str,
        sig: str,
        signode: nodes.Element,
        *,
        noindex: bool = False,
    ) -> None:
        """Add cross-reference target and entry to the general index."""
        domain = cast("TypeScriptDomain", self.env.get_domain("ts"))

        # Add target
        targetname = f"{self.objtype}-{name}"
        if targetname not in self.state.document.ids:
            signode["names"].append(targetname)
            signode["ids"].append(targetname)
            signode["first"] = not self.names
            self.state.document.note_explicit_target(signode)

            # Add to domain's object list
            domain.note_object(self.objtype, name, targetname, noindex=noindex)


class TSClass(TypeScriptObject):
    """Directive for TypeScript classes."""

    doc_field_types = [
        TypedField(
            "parameter",
            label=_("Parameters"),
            names=("param", "parameter", "arg", "argument"),
            typerolename="type",
            typenames=("paramtype", "type"),
        ),
        Field("returnvalue", label=_("Returns"), names=("returns", "return")),
        Field("returntype", label=_("Return type"), names=("rtype",)),
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def get_signature_prefix(self, _sig: str) -> str:
        """Return the signature prefix."""
        return "class "

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Parse the signature and return the class name."""
        signode.append(addnodes.desc_annotation("class ", "class "))

        # Handle generic parameters
        if "<" in sig:
            class_name = sig[: sig.index("<")]
            generic_part = sig[sig.index("<") :]
            signode.append(addnodes.desc_name(class_name, class_name))
            signode.append(addnodes.desc_annotation(generic_part, generic_part))
        else:
            signode.append(addnodes.desc_name(sig, sig))

        return sig


class TSInterface(TypeScriptObject):
    """Directive for TypeScript interfaces."""

    doc_field_types = [
        TypedField(
            "parameter",
            label=_("Parameters"),
            names=("param", "parameter", "arg", "argument"),
            typerolename="type",
            typenames=("paramtype", "type"),
        ),
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def get_signature_prefix(self, _sig: str) -> str:
        """Return the signature prefix."""
        return "interface "

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Parse the signature and return the interface name."""
        signode.append(addnodes.desc_annotation("interface ", "interface "))

        # Handle generic parameters
        if "<" in sig:
            interface_name = sig[: sig.index("<")]
            generic_part = sig[sig.index("<") :]
            signode.append(addnodes.desc_name(interface_name, interface_name))
            signode.append(addnodes.desc_annotation(generic_part, generic_part))
        else:
            signode.append(addnodes.desc_name(sig, sig))

        return sig


class TSMethod(TypeScriptObject):
    """Directive for TypeScript methods."""

    doc_field_types = [
        TypedField(
            "parameter",
            label=_("Parameters"),
            names=("param", "parameter", "arg", "argument"),
            typerolename="type",
            typenames=("paramtype", "type"),
        ),
        Field("returnvalue", label=_("Returns"), names=("returns", "return")),
        Field("returntype", label=_("Return type"), names=("rtype",)),
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def needs_arglist(self) -> bool:
        """Return True if this object needs an argument list."""
        return True

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Parse the signature and return the method name."""
        method_name = sig[: sig.index("(")] if "(" in sig else sig

        signode.append(addnodes.desc_sig_name(method_name, method_name))

        # Parse and format parameters properly
        parameters = parse_parameters_from_signature(sig)
        param_list = addnodes.desc_parameterlist()

        for param in parameters:
            param_node = addnodes.desc_parameter()

            # Add parameter name
            param_node.append(addnodes.desc_sig_name("", param["name"]))

            # Add optional marker if needed
            if param["optional"] == "true" and not param["default"]:
                param_node.append(nodes.Text("?"))

            # Add type annotation
            if param["type"]:
                param_node.append(nodes.Text(": "))
                param_node.append(addnodes.desc_sig_name("", param["type"]))

            # Add default value
            if param["default"]:
                param_node.append(nodes.Text(f" = {param['default']}"))

            param_list.append(param_node)

        signode.append(param_list)
        return method_name


class TSProperty(TypeScriptObject):
    """Directive for TypeScript properties."""

    doc_field_types = [
        Field("type", label=_("Type"), names=("type",)),
        Field("default", label=_("Default"), names=("default",)),
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Parse the signature and return the property name."""
        # Handle type annotation
        if ":" in sig:
            prop_name = sig[: sig.index(":")].strip()
            type_part = sig[sig.index(":") :].strip()
            signode.append(addnodes.desc_sig_name(prop_name, prop_name))
            type_annotation = addnodes.desc_annotation(type_part, type_part)
            signode.append(type_annotation)
        else:
            signode.append(addnodes.desc_sig_name(sig, sig))

        return sig.split(":")[0].strip() if ":" in sig else sig


class TSFunction(TypeScriptObject):
    """Directive for TypeScript functions."""

    doc_field_types = [
        TypedField(
            "parameter",
            label=_("Parameters"),
            names=("param", "parameter", "arg", "argument"),
            typerolename="type",
            typenames=("paramtype", "type"),
        ),
        Field("returnvalue", label=_("Returns"), names=("returns", "return")),
        Field("returntype", label=_("Return type"), names=("rtype",)),
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def get_signature_prefix(self, _sig: str) -> str:
        """Return the signature prefix."""
        return "function "

    def needs_arglist(self) -> bool:
        """Return True if this object needs an argument list."""
        return True

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Parse the signature and return the function name."""
        signode.append(addnodes.desc_annotation("function ", "function "))

        func_name = sig[: sig.index("(")] if "(" in sig else sig

        signode.append(addnodes.desc_sig_name(func_name, func_name))

        # Parse and format parameters properly
        parameters = parse_parameters_from_signature(sig)
        param_list = addnodes.desc_parameterlist()

        for param in parameters:
            param_node = addnodes.desc_parameter()

            # Add parameter name
            param_node.append(addnodes.desc_sig_name("", param["name"]))

            # Add optional marker if needed
            if param["optional"] == "true" and not param["default"]:
                param_node.append(nodes.Text("?"))

            # Add type annotation
            if param["type"]:
                param_node.append(nodes.Text(": "))
                param_node.append(addnodes.desc_sig_name("", param["type"]))

            # Add default value
            if param["default"]:
                param_node.append(nodes.Text(f" = {param['default']}"))

            param_list.append(param_node)

        signode.append(param_list)
        return func_name


class TSVariable(TypeScriptObject):
    """Directive for TypeScript variables/constants."""

    doc_field_types = [
        Field("type", label=_("Type"), names=("type",)),
        Field("value", label=_("Value"), names=("value",)),
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def get_signature_prefix(self, _sig: str) -> str:
        """Return the signature prefix for variables."""
        # Could be 'const', 'let', or 'var'
        return ""

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Parse the signature and return the variable name."""
        # Handle type annotation and value
        parts = sig.split("=", 1)
        name_and_type = parts[0].strip()

        if ":" in name_and_type:
            var_name = name_and_type[: name_and_type.index(":")].strip()
            type_part = name_and_type[name_and_type.index(":") :].strip()
            signode.append(addnodes.desc_name(var_name, var_name))
            type_annotation = addnodes.desc_annotation(type_part, type_part)
            signode.append(type_annotation)
        else:
            signode.append(addnodes.desc_name(name_and_type, name_and_type))

        if len(parts) > 1:
            signode.append(
                addnodes.desc_annotation(
                    " = " + parts[1].strip(),
                    " = " + parts[1].strip(),
                )
            )

        return sig.split(":")[0].split("=")[0].strip()


class TSXRefRole(XRefRole):
    """Cross-reference role for TypeScript objects."""

    def process_link(
        self,
        env: BuildEnvironment,
        refnode: nodes.Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> tuple[str, str]:
        """Process the link and return the title and target."""
        if not has_explicit_title:
            title = title.lstrip(".")
        return title, target


class TSParamRole(SphinxRole):
    """Role for TypeScript parameter names."""

    def run(self) -> tuple[list[Node], list[system_message]]:
        """Run the role."""
        node = inline(classes=["sig-name", "descname"])
        node += Text(self.text)

        return [node], []


class TSEnum(TypeScriptObject):
    """Directive for TypeScript enums."""

    doc_field_types = [
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def get_signature_prefix(self, _sig: str) -> str:
        """Return the signature prefix."""
        return "enum "

    def handle_signature(self, sig: str, signode: nodes.Element) -> str:
        """Parse the signature and return the enum name."""
        signode.append(addnodes.desc_annotation("enum ", "enum "))

        # Handle modifiers (const, declare, export)
        parts = sig.split()
        enum_name = parts[-1]  # Last part is the enum name

        # Add modifiers
        for part in parts[:-1]:
            if part in ("const", "declare", "export"):
                signode.append(addnodes.desc_annotation(f"{part} ", f"{part} "))

        signode.append(addnodes.desc_name(enum_name, enum_name))
        return enum_name


class TypeScriptDomain(Domain):
    """TypeScript domain."""

    name = "ts"
    label = "TypeScript"

    object_types = {
        "class": ObjType("class", "class", "obj"),
        "interface": ObjType("interface", "interface", "obj"),
        "enum": ObjType("enum", "enum", "obj"),
        "enum_member": ObjType("enum member", "enum_member", "obj"),
        "method": ObjType("method", "meth", "method", "obj"),
        "property": ObjType("property", "prop", "property", "obj"),
        "function": ObjType("function", "func", "function", "obj"),
        "variable": ObjType("variable", "var", "variable", "obj"),
        "type": ObjType("type", "type", "type", "obj"),
    }

    directives = {
        "class": TSClass,
        "interface": TSInterface,
        "enum": TSEnum,
        "method": TSMethod,
        "property": TSProperty,
        "function": TSFunction,
        "variable": TSVariable,
        "type": TSVariable,  # Type aliases use same directive as variables
    }

    roles = {
        "class": TSXRefRole(),
        "interface": TSXRefRole(),
        "enum": TSXRefRole(),
        "enum_member": TSXRefRole(),
        "meth": TSXRefRole(),
        "prop": TSXRefRole(),
        "func": TSXRefRole(),
        "var": TSXRefRole(),
        "type": TSXRefRole(),
        "obj": TSXRefRole(),
        "param": TSParamRole(),
    }

    initial_data = {
        "objects": {},
    }

    def clear_doc(self, docname: str) -> None:
        """Remove traces of a document in the domain-specific inventories."""
        for obj_type in self.object_types:
            if obj_type in self.data["objects"]:
                self.data["objects"][obj_type] = {
                    name: obj_data
                    for name, obj_data in self.data["objects"][obj_type].items()
                    if obj_data[0] != docname
                }

    def merge_domaindata(
        self,
        docnames: Iterable[str],
        otherdata: dict[str, Any],
    ) -> None:
        """Merge in data regarding docnames from a different domain."""
        for obj_type in self.object_types:
            if obj_type in otherdata["objects"]:
                for name, obj_data in otherdata["objects"][obj_type].items():
                    fn = obj_data[0]  # First element is always the docname
                    if fn in docnames:
                        if obj_type not in self.data["objects"]:
                            self.data["objects"][obj_type] = {}
                        self.data["objects"][obj_type][name] = obj_data

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: nodes.Element,
        contnode: nodes.Element,
    ) -> reference | None:
        """Resolve cross-references."""
        logger = logging.getLogger(__name__)
        logger.debug("Resolving TypeScript xref: %s:%s", typ, target)

        # Handle method and property references with class/interface prefix
        # such as Class.method
        if "." in target and (typ in ["meth", "prop", "method", "property"]):
            class_name, member_name = target.split(".", 1)

            # First check if the qualified name exists directly
            role_to_objtype = {
                "meth": "method",
                "prop": "property",
                "method": "method",
                "property": "property",
            }
            obj_type = role_to_objtype.get(typ)

            if (
                obj_type
                and obj_type in self.data["objects"]
                and target in self.data["objects"][obj_type]
            ):
                obj_data = self.data["objects"][obj_type][target]
                docname = obj_data[0]
                return make_refnode(
                    builder,
                    fromdocname,
                    docname,
                    f"{obj_type}-{target}",
                    contnode,
                    target,
                )

        # Map role to object type
        if typ == "obj":
            # Search in all object types
            for obj_type in self.object_types:
                if (
                    obj_type in self.data["objects"]
                    and target in self.data["objects"][obj_type]
                ):
                    obj_data = self.data["objects"][obj_type][target]
                    docname = obj_data[0]
                    target_id = target
                    display_text = target
                    if "." in target and obj_type in ["method", "property"]:
                        # If it's a qualified name, use the full name for ID
                        target_id = target
                        # But extract just the member name for display
                        display_text = target.split(".")[-1]
                    return make_refnode(
                        builder,
                        fromdocname,
                        docname,
                        f"{obj_type}-{target_id}",
                        contnode,
                        display_text,
                    )
        else:
            # Map specific role to object type
            role_to_objtype = {
                "class": "class",
                "interface": "interface",
                "meth": "method",
                "prop": "property",
                "func": "function",
                "var": "variable",
            }

            obj_type = role_to_objtype.get(typ)
            if (
                obj_type
                and obj_type in self.data["objects"]
                and target in self.data["objects"][obj_type]
            ):
                obj_data = self.data["objects"][obj_type][target]
                docname = obj_data[0]
                target_id = target
                display_text = target
                if "." in target and obj_type in ["method", "property"]:
                    # If it's a qualified name, use the full name for ID
                    target_id = target
                    # But extract just the member name for display
                    display_text = target.split(".")[-1]
                return make_refnode(
                    builder,
                    fromdocname,
                    docname,
                    f"{obj_type}-{target_id}",
                    contnode,
                    display_text,
                )

            # Fallback: if looking for a property but it's registered as a
            # method (e.g., getter/setter properties in TypeScript)
            if (
                typ == "prop"
                and "method" in self.data["objects"]
                and target in self.data["objects"]["method"]
            ):
                obj_data = self.data["objects"]["method"][target]
                docname = obj_data[0]
                target_id = target
                display_text = target
                if "." in target:
                    # If it's a qualified name, use the full name for ID
                    target_id = target
                    # But extract just the member name for display
                    display_text = target.split(".")[-1]
                return make_refnode(
                    builder,
                    fromdocname,
                    docname,
                    f"method-{target_id}",
                    contnode,
                    display_text,
                )

        logger.debug("TypeScript xref not found: %s:%s", typ, target)
        return None

    def resolve_any_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        target: str,
        node: nodes.Element,
        contnode: nodes.Element,
    ) -> list[tuple[str, reference]]:
        """Resolve any cross-reference (used for 'any' role)."""
        results = []

        for obj_type in self.object_types:
            if (
                obj_type in self.data["objects"]
                and target in self.data["objects"][obj_type]
            ):
                obj_data = self.data["objects"][obj_type][target]
                docname = obj_data[0]
                # Check if we should include this in results (not noindex)
                if (
                    len(obj_data) < OBJDATA_TUPLE_LENGTH
                    or not obj_data[OBJDATA_NOINDEX_INDEX]
                ):
                    refnode = make_refnode(
                        builder,
                        fromdocname,
                        docname,
                        f"{obj_type}-{target}",
                        contnode,
                        target,
                    )
                    results.append((f"ts:{obj_type}", refnode))

        return results

    def get_objects(self) -> Iterator[tuple[str, str, str, str, str, int]]:
        """Return an iterable of "object descriptions"."""
        objects_list = []
        for obj_type, objects in self.data["objects"].items():
            for name, obj_data in objects.items():
                # Unpack object data with support for older format
                if len(obj_data) >= OBJDATA_TUPLE_LENGTH:
                    docname, synopsis, noindex = obj_data
                else:
                    docname, synopsis = obj_data
                    noindex = False

                # Only add objects that shouldn't be hidden from TOC
                if not noindex:
                    objects_list.append(
                        (
                            name,
                            name,
                            obj_type,
                            docname,
                            f"{obj_type}-{name}",
                            1,
                        )
                    )

        # Sort objects by name (the first element in the tuple)
        objects_list.sort(key=lambda x: x[0])
        yield from objects_list

    def get_full_qualified_name(self, node: nodes.Element) -> str | None:
        """Get the fully qualified name of a node."""
        # This would need to be implemented based on the node structure
        return None

    def note_object(
        self,
        obj_type: str,
        name: str,
        _target: str,
        _location: nodes.Element | None = None,
        *,
        noindex: bool = False,
    ) -> None:
        """Note a TypeScript object for cross-referencing.

        Args:
            obj_type: The type of object (class, method, property, etc.)
            name: The name of the object
            _target: Unused target parameter
            _location: Unused location parameter
            noindex: If True, the object won't appear in the global index/TOC

        """
        if obj_type not in self.data["objects"]:
            self.data["objects"][obj_type] = {}

        docname = getattr(self.env, "docname", "")
        self.data["objects"][obj_type][name] = (docname, "", noindex)
