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
    is_abstract: bool = False


@dataclass
class CodeClass:
    """A class discovered in the source tree by the code inspector."""

    name: str
    module_path: str
    attributes: set[str] = field(default_factory=set)
    methods: set[str] = field(default_factory=set)
    stub_methods: set[str] = field(default_factory=set)
    is_abstract: bool = False

    @property
    def member_names(self) -> set[str]:
        """Every attribute and method name defined on the class."""
        return self.attributes | self.methods

    @property
    def has_stub(self) -> bool:
        """True when any method body is only ``pass``/``...``/``NotImplementedError``."""
        return bool(self.stub_methods)


@dataclass(frozen=True)
class UmlRelationship:
    """A directed dependency between two UML classes, ``source`` -> ``target``.

    ``source`` depends on ``target`` (needs it to be built first). Parsed from a
    PlantUML relationship line; arrowhead direction is normalised so ``source``
    is always the dependent side.
    """

    source: str
    target: str


@dataclass
class ClassComparison:
    """The outcome of comparing one UML class against the code."""

    uml_class: UmlClass
    status: ImplementationStatus
    missing_members: list[UmlMember] = field(default_factory=list)


@dataclass(frozen=True)
class BalanceEntry:
    """Member-count balance for one class: UML-declared vs. code-implemented.

    ``diff`` is ``uml_count - code_count``: positive means the UML declares more
    members than the code implements (unbuilt surface), negative means the code
    carries members the UML never declared (undocumented surface).
    """

    name: str
    uml_count: int
    code_count: int

    @property
    def diff(self) -> int:
        """UML-declared minus code-implemented member count."""
        return self.uml_count - self.code_count


@dataclass
class OrderedClass:
    """A pending class placed in build order, with its unbuilt dependencies.

    ``depends_on`` lists the names of the *other pending classes* this one
    depends on — already-implemented dependencies are omitted since they are
    done. An empty list means the class is a leaf and can be built immediately.
    """

    comparison: ClassComparison
    depends_on: list[str] = field(default_factory=list)
