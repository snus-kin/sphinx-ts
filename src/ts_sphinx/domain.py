"""TypeScript Sphinx Domain.

Provides a Sphinx domain for TypeScript with roles and object types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from docutils.nodes import Element as DocElement
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from docutils.parsers.rst import Directive
from sphinx.domains import Domain, ObjType
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docfields import Field, TypedField
from sphinx.util.nodes import make_refnode
from typing import AbstractSet

from sphinx.util.typing import RoleFunction
from typing import cast

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docutils.nodes import Element, reference
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)


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

    def handle_signature(self, sig: str, signode: Element) -> str:
        """Transform a signature into RST nodes."""
        return sig

    def add_target_and_index(
        self, name: str, sig: str, signode: Element
    ) -> None:
        """Add cross-reference target and entry to the general index."""
        domain = cast(TypeScriptDomain, self.env.get_domain("ts"))

        # Add target
        targetname = f"{self.objtype}-{name}"
        if targetname not in self.state.document.ids:
            signode["names"].append(targetname)
            signode["ids"].append(targetname)
            signode["first"] = not self.names
            self.state.document.note_explicit_target(signode)

            # Add to domain's object list
            domain.note_object(self.objtype, name, targetname)


class TSClass(TypeScriptObject):
    """Directive for TypeScript classes."""

    doc_field_types: list[Field] = [
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

    def handle_signature(self, sig: str, signode: Element) -> str:
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

    doc_field_types: list[Field] = [
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

    def handle_signature(self, sig: str, signode: Element) -> str:
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

    doc_field_types: list[Field] = [
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

    def handle_signature(self, sig: str, signode: Element) -> str:
        """Parse the signature and return the method name."""
        # Simple parsing - real implementation would use more sophisticated
        if "(" in sig:
            method_name = sig[: sig.index("(")]
            args_part = sig[sig.index("(") :]
        else:
            method_name = sig
            args_part = "()"

        signode.append(addnodes.desc_name(method_name, method_name))
        signode.append(addnodes.desc_parameterlist())

        # Parse arguments
        if args_part != "()":
            # This is simplified - real implementation would parse properly
            param_node = addnodes.desc_parameter(
                args_part[1:-1], args_part[1:-1]
            )
            # Cast to proper node type for append operation
            param_list = signode[-1]
            if isinstance(param_list, DocElement):
                param_list.append(param_node)
            else:
                signode[-1] += param_node

        return method_name


class TSProperty(TypeScriptObject):
    """Directive for TypeScript properties."""

    doc_field_types: list[Field] = [
        Field("type", label=_("Type"), names=("type",)),
        Field("default", label=_("Default"), names=("default",)),
        Field("example", label=_("Example"), names=("example",)),
        Field("since", label=_("Since"), names=("since",)),
        Field("deprecated", label=_("Deprecated"), names=("deprecated",)),
    ]

    def handle_signature(self, sig: str, signode: Element) -> str:
        """Parse the signature and return the property name."""
        # Handle type annotation
        if ":" in sig:
            prop_name = sig[: sig.index(":")].strip()
            type_part = sig[sig.index(":") :].strip()
            signode.append(addnodes.desc_name(prop_name, prop_name))
            signode.append(addnodes.desc_annotation(type_part, type_part))
        else:
            signode.append(addnodes.desc_name(sig, sig))

        return sig.split(":")[0].strip() if ":" in sig else sig


class TSFunction(TypeScriptObject):
    """Directive for TypeScript functions."""

    doc_field_types: list[Field] = [
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

    def handle_signature(self, sig: str, signode: Element) -> str:
        """Parse the signature and return the function name."""
        signode.append(addnodes.desc_annotation("function ", "function "))

        if "(" in sig:
            func_name = sig[: sig.index("(")]
            args_part = sig[sig.index("(") :]
        else:
            func_name = sig
            args_part = "()"

        signode.append(addnodes.desc_name(func_name, func_name))
        signode.append(addnodes.desc_parameterlist())

        # Parse arguments (simplified)
        if args_part != "()":
            param_node = addnodes.desc_parameter(
                args_part[1:-1], args_part[1:-1]
            )
            # Cast to proper node type for append operation
            param_list = signode[-1]
            if isinstance(param_list, DocElement):
                param_list.append(param_node)
            else:
                signode[-1] += param_node

        return func_name


class TSVariable(TypeScriptObject):
    """Directive for TypeScript variables/constants."""

    doc_field_types: list[Field] = [
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

    def handle_signature(self, sig: str, signode: Element) -> str:
        """Parse the signature and return the variable name."""
        # Handle type annotation and value
        parts = sig.split("=", 1)
        name_and_type = parts[0].strip()

        if ":" in name_and_type:
            var_name = name_and_type[: name_and_type.index(":")].strip()
            type_part = name_and_type[name_and_type.index(":") :].strip()
            signode.append(addnodes.desc_name(var_name, var_name))
            signode.append(addnodes.desc_annotation(type_part, type_part))
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
        refnode: Element,
        has_explicit_title: bool,
        title: str,
        target: str,
    ) -> tuple[str, str]:
        """Process the link and return the title and target."""
        if not has_explicit_title:
            title = title.lstrip(".")
        return title, target


class TypeScriptDomain(Domain):
    """TypeScript domain."""

    name = "ts"
    label = "TypeScript"

    object_types: dict[str, ObjType] = {
        "class": ObjType(_("class"), "class", "obj"),
        "interface": ObjType(_("interface"), "interface", "obj"),
        "method": ObjType(_("method"), "meth", "obj"),
        "property": ObjType(_("property"), "prop", "obj"),
        "function": ObjType(_("function"), "func", "obj"),
        "variable": ObjType(_("variable"), "var", "obj"),
    }

    directives: dict[str, type[Directive]] = {
        "class": TSClass,
        "interface": TSInterface,
        "method": TSMethod,
        "property": TSProperty,
        "function": TSFunction,
        "variable": TSVariable,
    }

    roles: dict[str, RoleFunction | TSXRefRole] = {
        "class": TSXRefRole(),
        "interface": TSXRefRole(),
        "meth": TSXRefRole(),
        "prop": TSXRefRole(),
        "func": TSXRefRole(),
        "var": TSXRefRole(),
        "obj": TSXRefRole(),
    }

    initial_data: dict[str, Any] = {
        "objects": {},
    }

    def clear_doc(self, docname: str) -> None:
        """Remove traces of a document in the domain-specific inventories."""
        for obj_type in self.object_types:
            if obj_type in self.data["objects"]:
                self.data["objects"][obj_type] = {
                    name: (fn, synopsis)
                    for name, (fn, synopsis) in self.data["objects"][
                        obj_type
                    ].items()
                    if fn != docname
                }

    def merge_domaindata(
        self, docnames: AbstractSet[str], otherdata: dict[str, Any]
    ) -> None:
        """Merge in data regarding docnames from a different domain."""
        for obj_type in self.object_types:
            if obj_type in otherdata["objects"]:
                for name, (fn, synopsis) in otherdata["objects"][
                    obj_type
                ].items():
                    if fn in docnames:
                        if obj_type not in self.data["objects"]:
                            self.data["objects"][obj_type] = {}
                        self.data["objects"][obj_type][name] = (fn, synopsis)

    def resolve_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        typ: str,
        target: str,
        node: Element,
        contnode: Element,
    ) -> reference | None:
        """Resolve cross-references."""
        # Map role to object type
        if typ == "obj":
            # Search in all object types
            for obj_type in self.object_types:
                if (
                    obj_type in self.data["objects"]
                    and target in self.data["objects"][obj_type]
                ):
                    docname, synopsis = self.data["objects"][obj_type][target]
                    return make_refnode(
                        builder,
                        fromdocname,
                        docname,
                        f"{obj_type}-{target}",
                        contnode,
                        target,
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
                docname, synopsis = self.data["objects"][obj_type][target]
                return make_refnode(
                    builder,
                    fromdocname,
                    docname,
                    f"{obj_type}-{target}",
                    contnode,
                    target,
                )

        return None

    def resolve_any_xref(
        self,
        env: BuildEnvironment,
        fromdocname: str,
        builder: Builder,
        target: str,
        node: Element,
        contnode: Element,
    ) -> list[tuple[str, reference]]:
        """Resolve any cross-reference (used for 'any' role)."""
        results = []

        for obj_type in self.object_types:
            if (
                obj_type in self.data["objects"]
                and target in self.data["objects"][obj_type]
            ):
                docname, synopsis = self.data["objects"][obj_type][target]
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
        for obj_type, objects in self.data["objects"].items():
            for name, (docname, _synopsis) in objects.items():
                yield (name, name, obj_type, docname, f"{obj_type}-{name}", 1)

    def get_full_qualified_name(self, node: Element) -> str | None:
        """Get the fully qualified name of a node."""
        # This would need to be implemented based on the node structure
        return None

    def note_object(
        self,
        obj_type: str,
        name: str,
        _target: str,
        _location: Element | None = None,
    ) -> None:
        """Note a TypeScript object for cross-referencing."""
        if obj_type not in self.data["objects"]:
            self.data["objects"][obj_type] = {}

        docname = getattr(self.env, "docname", "")
        self.data["objects"][obj_type][name] = (docname, "")
