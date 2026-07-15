"""Tests for the PlantUML writer."""

from classpy.adapters.puml.parser import PumlParser
from classpy.adapters.puml.writer import PumlWriter
from classpy.domain.models import (
    ClassComparison,
    ImplementationStatus,
    UmlClass,
)


def _comparison(name, status, stereotype="planned"):
    uml = UmlClass(name=name, package="", stereotype=stereotype, members=[])
    return ClassComparison(uml_class=uml, status=status)


def test_replaces_stereotype_on_class_line():
    text = "package X {\n    class Widget <<planned>> {\n        +render()\n    }\n}\n"
    out = PumlWriter().apply(
        text, [_comparison("Widget", ImplementationStatus.IMPLEMENTED)]
    )
    assert "class Widget <<implemented>> {" in out
    assert "<<planned>>" not in out


def test_preserves_members_and_layout():
    text = "    class Widget <<planned>> {\n        +render()\n        +resize()\n    }\n"
    out = PumlWriter().apply(
        text, [_comparison("Widget", ImplementationStatus.PARTIAL)]
    )
    assert "        +render()" in out
    assert "        +resize()" in out
    assert out.endswith("\n")


def test_enum_declaration_is_updated():
    text = "enum MemberKind <<planned>> {\n    ATTRIBUTE\n}\n"
    out = PumlWriter().apply(
        text, [_comparison("MemberKind", ImplementationStatus.IMPLEMENTED)]
    )
    assert "enum MemberKind <<implemented>> {" in out


def test_unlisted_classes_are_untouched():
    text = "class A <<planned>> {\n}\nclass B <<partial>> {\n}\n"
    out = PumlWriter().apply(
        text, [_comparison("A", ImplementationStatus.IMPLEMENTED)]
    )
    assert "class A <<implemented>> {" in out
    assert "class B <<partial>> {" in out


def test_relationship_lines_never_rewritten():
    text = "class A <<planned>> {\n}\nA --> B\n"
    out = PumlWriter().apply(
        text, [_comparison("A", ImplementationStatus.IMPLEMENTED)]
    )
    assert "A --> B" in out


def test_roundtrip_parse_apply_reparse():
    text = (
        "package P {\n"
        "    class Widget <<planned>> {\n"
        "        +render()\n"
        "    }\n"
        "}\n"
    )
    out = PumlWriter().apply(
        text, [_comparison("Widget", ImplementationStatus.IMPLEMENTED)]
    )
    reparsed = {c.name: c for c in PumlParser().parse(out)}
    assert reparsed["Widget"].stereotype == "implemented"
    assert [m.name for m in reparsed["Widget"].members] == ["render"]
