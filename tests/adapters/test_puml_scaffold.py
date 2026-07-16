"""Tests for the empty-diagram scaffold adapter."""

from classpy.adapters.puml.parser import PumlParser
from classpy.adapters.puml.scaffold import EMPTY_TEMPLATE, PumlScaffold


def test_create_file_writes_template_and_makes_parent_dirs(tmp_path):
    target = tmp_path / "docs" / "class.puml"
    created = PumlScaffold().create_file(target)
    assert created is True
    assert target.read_text(encoding="utf-8") == EMPTY_TEMPLATE


def test_create_file_leaves_an_existing_file_untouched(tmp_path):
    target = tmp_path / "class.puml"
    target.write_text("existing", encoding="utf-8")
    created = PumlScaffold().create_file(target)
    assert created is False
    assert target.read_text(encoding="utf-8") == "existing"


def test_template_has_the_three_layers_and_no_classes():
    for layer in ("Service Layer", "Model Domain Layer", "Adapter Layer"):
        assert layer in EMPTY_TEMPLATE
    # The scaffold keeps the tags/legend but carries no classes to sync.
    assert "<<implemented>>" in EMPTY_TEMPLATE
    assert PumlParser().parse(EMPTY_TEMPLATE) == []
