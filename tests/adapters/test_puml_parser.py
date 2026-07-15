"""Tests for the PlantUML parser."""

from classpy.adapters.puml.parser import PumlParser
from classpy.domain.models import MemberKind

SAMPLE = """
@startuml
skinparam class {
    BackgroundColor<<implemented>> #D5F5D5
}
legend right
|= Colour |
endlegend

class numpy <<external>>

package "Service Layer" {
    class SyncService <<planned>> {
        +parser
        +sync()
        +status()
    }
    class Cli <<planned>> {
        +sync()
    }
    Cli --> SyncService
}

package "Model Domain Layer" {
    package "Models" {
        enum MemberKind <<implemented>> {
            ATTRIBUTE
            METHOD
        }
        class UmlMember <<partial>> {
            +name: str
            -_hidden: int
            +describe(kind): str
        }
        UmlMember ..> MemberKind
    }
}
@enduml
"""


def _by_name(classes):
    return {c.name: c for c in classes}


def test_parses_all_declared_classes():
    classes = _by_name(PumlParser().parse(SAMPLE))
    assert set(classes) == {
        "numpy",
        "SyncService",
        "Cli",
        "MemberKind",
        "UmlMember",
    }


def test_captures_stereotype():
    classes = _by_name(PumlParser().parse(SAMPLE))
    assert classes["SyncService"].stereotype == "planned"
    assert classes["MemberKind"].stereotype == "implemented"
    assert classes["numpy"].stereotype == "external"


def test_external_class_is_top_level_with_no_package():
    classes = _by_name(PumlParser().parse(SAMPLE))
    assert classes["numpy"].package == ""
    assert classes["numpy"].members == []


def test_nested_package_path():
    classes = _by_name(PumlParser().parse(SAMPLE))
    assert classes["UmlMember"].package == "Model Domain Layer/Models"
    assert classes["SyncService"].package == "Service Layer"


def test_member_kinds_and_names():
    classes = _by_name(PumlParser().parse(SAMPLE))
    members = {m.name: m.kind for m in classes["UmlMember"].members}
    assert members == {
        "name": MemberKind.ATTRIBUTE,
        "_hidden": MemberKind.ATTRIBUTE,
        "describe": MemberKind.METHOD,
    }


def test_enum_values_parsed_as_attributes():
    classes = _by_name(PumlParser().parse(SAMPLE))
    members = {m.name: m.kind for m in classes["MemberKind"].members}
    assert members == {
        "ATTRIBUTE": MemberKind.ATTRIBUTE,
        "METHOD": MemberKind.ATTRIBUTE,
    }


def test_relationship_lines_are_not_classes():
    names = {c.name for c in PumlParser().parse(SAMPLE)}
    assert "-->" not in names and ".." not in names


def test_abstract_and_interface_flag_is_abstract():
    text = """
    @startuml
    abstract class Repository {
        +get()
    }
    interface Reader {
        +read()
    }
    class Concrete {
        +run()
    }
    @enduml
    """
    classes = _by_name(PumlParser().parse(text))
    assert classes["Repository"].is_abstract is True
    assert classes["Reader"].is_abstract is True
    assert classes["Concrete"].is_abstract is False
    # keyword capture must not corrupt names, stereotypes, or members
    assert [m.name for m in classes["Repository"].members] == ["get"]
