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


def test_detects_stub_method_bodies(tmp_path):
    _write(
        tmp_path,
        "pkg/service.py",
        '''
        class Service:
            def do_pass(self):
                pass

            def do_ellipsis(self): ...

            def do_raise(self):
                raise NotImplementedError

            def do_raise_call(self):
                raise NotImplementedError("later")

            def documented_stub(self):
                """Docstring then a stub."""
                ...

            def real(self):
                return 42
        ''',
    )
    service = _by_name(CodeInspector().inspect(tmp_path))["Service"]
    assert service.stub_methods == {
        "do_pass",
        "do_ellipsis",
        "do_raise",
        "do_raise_call",
        "documented_stub",
    }
    assert service.has_stub is True


def test_non_stub_methods_are_not_flagged(tmp_path):
    _write(
        tmp_path,
        "pkg/calc.py",
        '''
        class Calc:
            def add(self, a, b):
                return a + b

            def only_docstring(self):
                """Not a stub: a docstring alone is a real (returning-None) body."""
        ''',
    )
    calc = _by_name(CodeInspector().inspect(tmp_path))["Calc"]
    assert calc.stub_methods == set()
    assert calc.has_stub is False


def test_syntax_errors_are_skipped(tmp_path):
    _write(tmp_path, "bad.py", "class Broken(:\n")
    _write(tmp_path, "good.py", "class Good: pass\n")
    names = {c.name for c in CodeInspector().inspect(tmp_path)}
    assert names == {"Good"}
