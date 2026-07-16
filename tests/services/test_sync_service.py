"""End-to-end tests for the sync service against a temp project."""

from textwrap import dedent

from classpy.adapters.puml.parser import PumlParser
from classpy.domain.models import ImplementationStatus
from classpy.services.sync_service import SyncService

DIAGRAM = dedent(
    """
    @startuml
    package "Service Layer" {
        class Done <<planned>> {
            +run()
        }
        class Half <<planned>> {
            +run()
            +stop()
        }
        class Missing <<planned>> {
            +run()
        }
        Missing --> Half
    }
    class numpy <<external>> {
        +array()
    }
    @enduml
    """
).strip()


def _make_project(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    puml = docs / "class.puml"
    puml.write_text(DIAGRAM, encoding="utf-8")

    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True)
    (src / "pkg" / "done.py").write_text(
        "class Done:\n    def run(self):\n        return 1\n", encoding="utf-8"
    )
    (src / "pkg" / "half.py").write_text(
        "class Half:\n    def run(self):\n        return 1\n", encoding="utf-8"
    )
    return puml, src


def _statuses(report):
    return {c.uml_class.name: c.status for c in report.comparisons}


def test_status_classifies_each_class(tmp_path):
    puml, src = _make_project(tmp_path)
    report = SyncService().status(puml, src)
    statuses = _statuses(report)
    assert statuses["Done"] is ImplementationStatus.IMPLEMENTED
    assert statuses["Half"] is ImplementationStatus.PARTIAL
    assert statuses["Missing"] is ImplementationStatus.PLANNED
    assert statuses["numpy"] is ImplementationStatus.EXTERNAL


def test_status_does_not_write(tmp_path):
    puml, src = _make_project(tmp_path)
    before = puml.read_text(encoding="utf-8")
    SyncService().status(puml, src)
    assert puml.read_text(encoding="utf-8") == before


def test_sync_repaints_the_diagram(tmp_path):
    puml, src = _make_project(tmp_path)
    SyncService().sync(puml, src)
    reparsed = {c.name: c for c in PumlParser().parse_file(puml)}
    assert reparsed["Done"].stereotype == "implemented"
    assert reparsed["Half"].stereotype == "partial"
    assert reparsed["Missing"].stereotype == "planned"
    assert reparsed["numpy"].stereotype == "external"


def test_report_flags_and_counts(tmp_path):
    puml, src = _make_project(tmp_path)
    report = SyncService().status(puml, src)
    assert report.is_stale is True
    changed_names = {c.uml_class.name for c in report.changed}
    assert changed_names == {"Done", "Half"}
    assert report.counts[ImplementationStatus.IMPLEMENTED] == 1
    assert report.counts[ImplementationStatus.PARTIAL] == 1


def test_second_sync_is_idempotent(tmp_path):
    puml, src = _make_project(tmp_path)
    SyncService().sync(puml, src)
    report = SyncService().sync(puml, src)
    assert report.is_stale is False


def _pending_names(report):
    return [o.comparison.uml_class.name for o in report.ordered]


def test_pending_lists_only_planned_by_default(tmp_path):
    puml, src = _make_project(tmp_path)
    report = SyncService().pending(puml, src)
    # Done is implemented, Half is partial, numpy external -> only Missing.
    assert _pending_names(report) == ["Missing"]
    assert report.ordered[0].depends_on == []  # Half is out of scope


def test_pending_includes_partial_when_requested(tmp_path):
    puml, src = _make_project(tmp_path)
    report = SyncService().pending(puml, src, include_partial=True)
    # Missing depends on Half, so Half (the leaf) must come first.
    assert _pending_names(report) == ["Half", "Missing"]
    by_name = {o.comparison.uml_class.name: o for o in report.ordered}
    assert by_name["Missing"].depends_on == ["Half"]
