"""Tests for the build-order dependency sorter."""

from classpy.domain.dependency import DependencyOrderer
from classpy.domain.models import (
    ClassComparison,
    ImplementationStatus,
    UmlClass,
    UmlRelationship,
)


def _pending(*names):
    return [
        ClassComparison(
            UmlClass(name=name, package="", stereotype="planned"),
            ImplementationStatus.PLANNED,
        )
        for name in names
    ]


def _order(comparisons, relationships):
    ordered = DependencyOrderer().order(comparisons, relationships)
    return [o.comparison.uml_class.name for o in ordered]


def test_leaves_come_before_their_dependents():
    pending = _pending("Cli", "Service", "Parser")
    rels = [
        UmlRelationship("Cli", "Service"),
        UmlRelationship("Service", "Parser"),
    ]
    assert _order(pending, rels) == ["Parser", "Service", "Cli"]


def test_dependencies_on_implemented_classes_are_ignored():
    # Parser is already implemented (not in the pending set), so it must not
    # appear and must not hold back the class that depends on it.
    pending = _pending("Service")
    rels = [UmlRelationship("Service", "Parser")]
    ordered = DependencyOrderer().order(pending, rels)
    assert [o.comparison.uml_class.name for o in ordered] == ["Service"]
    assert ordered[0].depends_on == []


def test_reports_pending_dependencies():
    pending = _pending("A", "B")
    rels = [UmlRelationship("A", "B")]
    ordered = DependencyOrderer().order(pending, rels)
    by_name = {o.comparison.uml_class.name: o for o in ordered}
    assert by_name["A"].depends_on == ["B"]
    assert by_name["B"].depends_on == []


def test_ties_broken_by_name_for_stable_output():
    pending = _pending("Zulu", "Alpha", "Mike")
    assert _order(pending, []) == ["Alpha", "Mike", "Zulu"]


def test_cycle_is_broken_not_dropped():
    pending = _pending("X", "Y")
    rels = [UmlRelationship("X", "Y"), UmlRelationship("Y", "X")]
    result = _order(pending, rels)
    assert sorted(result) == ["X", "Y"]
    assert len(result) == 2
