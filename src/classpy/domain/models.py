"""Core domain models shared across every layer.

These are plain data structures with no behaviour that touches the outside world.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ImplementationStatus(Enum):
    """Implementation state of a class, mapped to a PlantUML stereotype colour."""

    PLANNED = "planned"
    PARTIAL = "partial"
    IMPLEMENTED = "implemented"
    EXTERNAL = "external"

    @property
    def stereotype(self) -> str:
        """The ``<<...>>`` token this status renders as in the diagram."""
        return self.value


class MemberKind(Enum):
    """Whether a declared UML member is an attribute or a method."""

    ATTRIBUTE = "attribute"
    METHOD = "method"


@dataclass(frozen=True)
class UmlMember:
    """A single attribute or method declared on a UML class."""

    name: str
    kind: MemberKind


@dataclass
class UmlClass:
    """A class as declared in the ``.puml`` diagram.

    ``package`` is the ``/``-joined path of enclosing PlantUML packages, innermost
    last (e.g. ``"Model Domain Layer/Models"``).
    """

    name: str
    package: str
    stereotype: str
    members: list[UmlMember] = field(default_factory=list)


@dataclass
class CodeClass:
    """A class discovered in the source tree by the code inspector."""

    name: str
    module_path: str
    attributes: set[str] = field(default_factory=set)
    methods: set[str] = field(default_factory=set)

    @property
    def member_names(self) -> set[str]:
        """Every attribute and method name defined on the class."""
        return self.attributes | self.methods


@dataclass
class ClassComparison:
    """The outcome of comparing one UML class against the code."""

    uml_class: UmlClass
    status: ImplementationStatus
    missing_members: list[UmlMember] = field(default_factory=list)
