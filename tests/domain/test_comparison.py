"""Tests for the status comparison engine."""

from classpy.domain.comparison import StatusComparator
from classpy.domain.models import (
    CodeClass,
    ImplementationStatus,
    MemberKind,
    UmlClass,
    UmlMember,
)


def _uml(name, members=(), stereotype="planned"):
    return UmlClass(
        name=name,
        package="Model Domain Layer/Models",
        stereotype=stereotype,
        members=[UmlMember(m, MemberKind.METHOD) for m in members],
    )


def test_absent_code_class_is_planned():
    uml = _uml("Widget", ["render"])
    result = StatusComparator().compare(uml, None)
    assert result.status is ImplementationStatus.PLANNED
    assert [m.name for m in result.missing_members] == ["render"]


def test_all_members_present_is_implemented():
    uml = _uml("Widget", ["render", "resize"])
    code = CodeClass("Widget", "src/widget.py", methods={"render", "resize"})
    result = StatusComparator().compare(uml, code)
    assert result.status is ImplementationStatus.IMPLEMENTED
    assert result.missing_members == []


def test_some_members_missing_is_partial():
    uml = _uml("Widget", ["render", "resize"])
    code = CodeClass("Widget", "src/widget.py", methods={"render"})
    result = StatusComparator().compare(uml, code)
    assert result.status is ImplementationStatus.PARTIAL
    assert [m.name for m in result.missing_members] == ["resize"]


def test_memberless_present_class_is_implemented_not_partial():
    uml = _uml("Marker", [])
    code = CodeClass("Marker", "src/marker.py")
    result = StatusComparator().compare(uml, code)
    assert result.status is ImplementationStatus.IMPLEMENTED


def test_attribute_declared_matches_code_attribute():
    uml = UmlClass(
        "Point",
        "Model Domain Layer/Models",
        "planned",
        [UmlMember("x", MemberKind.ATTRIBUTE), UmlMember("y", MemberKind.ATTRIBUTE)],
    )
    code = CodeClass("Point", "src/point.py", attributes={"x", "y"})
    assert StatusComparator().compare(uml, code).status is ImplementationStatus.IMPLEMENTED


def test_external_class_left_untouched():
    uml = _uml("numpy", ["array"], stereotype="external")
    result = StatusComparator().compare(uml, None)
    assert result.status is ImplementationStatus.EXTERNAL
    assert result.missing_members == []
