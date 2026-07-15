"""Tests for name conversion and code-class matching."""

import pytest

from classpy.domain.locator import ClassLocator
from classpy.domain.models import CodeClass, UmlClass


@pytest.fixture
def locator():
    return ClassLocator()


def _uml(name, package="Adapter Layer/PlantUML"):
    return UmlClass(name=name, package=package, stereotype="planned", members=[])


@pytest.mark.parametrize(
    "name, expected",
    [
        ("SimulationRun", "simulation_run"),
        ("UmlClass", "uml_class"),
        ("PumlParser", "puml_parser"),
        ("HTTPClient", "http_client"),
        ("Cli", "cli"),
        ("A", "a"),
    ],
)
def test_to_snake_case(locator, name, expected):
    assert locator.to_snake_case(name) == expected


def test_expected_module(locator):
    assert locator.expected_module(_uml("SimulationRun")) == "simulation_run.py"


def test_select_returns_none_when_no_name_match(locator):
    code = [CodeClass("Other", "src/other.py")]
    assert locator.select(_uml("Widget"), code) is None


def test_select_single_name_match(locator):
    code = [CodeClass("Widget", "src/anywhere/widget.py")]
    assert locator.select(_uml("Widget"), code).module_path == "src/anywhere/widget.py"


def test_select_prefers_conventional_filename(locator):
    code = [
        CodeClass("PumlParser", "src/classpy/adapters/other.py"),
        CodeClass("PumlParser", "src/classpy/adapters/puml/puml_parser.py"),
    ]
    chosen = locator.select(_uml("PumlParser"), code)
    assert chosen.module_path.endswith("puml_parser.py")


def test_select_uses_package_hint_to_disambiguate(locator):
    code = [
        CodeClass("Parser", "src/classpy/services/parser.py"),
        CodeClass("Parser", "src/classpy/adapters/plant_uml/parser.py"),
    ]
    uml = _uml("Parser", package="Adapter Layer/PlantUML")
    chosen = locator.select(uml, code)
    assert "plant_uml" in chosen.module_path
