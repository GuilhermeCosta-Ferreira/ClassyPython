"""Tests for the ast-based code inspector."""

from textwrap import dedent

from classpy.adapters.code.inspector import CodeInspector


def _write(tmp_path, relative, source):
    file_path = tmp_path / relative
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(dedent(source), encoding="utf-8")
    return file_path


def _by_name(classes):
    return {c.name: c for c in classes}


def test_collects_methods_and_instance_attributes(tmp_path):
    _write(
        tmp_path,
        "pkg/widget.py",
        """
        class Widget:
            kind = "button"

            def __init__(self, label):
                self.label = label
                self._id = 0

            def render(self):
                return self.label
        """,
    )
    widget = _by_name(CodeInspector().inspect(tmp_path))["Widget"]
    assert widget.methods == {"__init__", "render"}
    assert widget.attributes == {"kind", "label", "_id"}


def test_collects_dataclass_annotations(tmp_path):
    _write(
        tmp_path,
        "pkg/point.py",
        """
        from dataclasses import dataclass

        @dataclass
        class Point:
            x: int
            y: int = 0
        """,
    )
    point = _by_name(CodeInspector().inspect(tmp_path))["Point"]
    assert point.attributes == {"x", "y"}


def test_collects_enum_members(tmp_path):
    _write(
        tmp_path,
        "pkg/color.py",
        """
        from enum import Enum

        class Color(Enum):
            RED = "red"
            BLUE = "blue"
        """,
    )
    color = _by_name(CodeInspector().inspect(tmp_path))["Color"]
    assert color.attributes == {"RED", "BLUE"}


def test_module_path_is_recorded(tmp_path):
    _write(tmp_path, "pkg/sub/thing.py", "class Thing: pass\n")
    thing = _by_name(CodeInspector().inspect(tmp_path))["Thing"]
    assert thing.module_path.endswith("pkg/sub/thing.py")


def test_syntax_errors_are_skipped(tmp_path):
    _write(tmp_path, "bad.py", "class Broken(:\n")
    _write(tmp_path, "good.py", "class Good: pass\n")
    names = {c.name for c in CodeInspector().inspect(tmp_path)}
    assert names == {"Good"}
