"""Tests for the Typer CLI."""

from textwrap import dedent

from typer.testing import CliRunner

from classpy.adapters.cli.app import build_app

runner = CliRunner()

DIAGRAM = dedent(
    """
    @startuml
    class Done <<planned>> {
        +run()
    }
    class Missing <<planned>> {
        +run()
    }
    Missing --> Done
    @enduml
    """
).strip()


def _project(tmp_path):
    puml = tmp_path / "class.puml"
    puml.write_text(DIAGRAM, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "done.py").write_text(
        "class Done:\n    def run(self):\n        return 1\n", encoding="utf-8"
    )
    return puml, src


def test_status_command_reports_without_writing(tmp_path):
    puml, src = _project(tmp_path)
    before = puml.read_text(encoding="utf-8")
    result = runner.invoke(
        build_app(), ["status", "--puml", str(puml), "--src", str(src)]
    )
    assert result.exit_code == 0
    assert "Done" in result.output
    assert puml.read_text(encoding="utf-8") == before


def test_sync_command_writes(tmp_path):
    puml, src = _project(tmp_path)
    result = runner.invoke(
        build_app(), ["sync", "--puml", str(puml), "--src", str(src)]
    )
    assert result.exit_code == 0
    assert "<<implemented>>" in puml.read_text(encoding="utf-8")


def test_check_flag_exits_nonzero_when_stale(tmp_path):
    puml, src = _project(tmp_path)
    result = runner.invoke(
        build_app(),
        ["sync", "--check", "--puml", str(puml), "--src", str(src)],
    )
    assert result.exit_code == 1
    # --check must not modify the file
    assert "<<implemented>>" not in puml.read_text(encoding="utf-8")


def test_check_flag_exits_zero_when_current(tmp_path):
    puml, src = _project(tmp_path)
    runner.invoke(build_app(), ["sync", "--puml", str(puml), "--src", str(src)])
    result = runner.invoke(
        build_app(),
        ["sync", "--check", "--puml", str(puml), "--src", str(src)],
    )
    assert result.exit_code == 0


def test_defaults_come_from_pyproject_config(tmp_path, monkeypatch):
    puml, src = _project(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        f'[tool.classpy]\npuml = "{puml.name}"\nsrc = "{src.name}"\n',
        encoding="utf-8",
    )
    # No --puml/--src flags: paths must be resolved from [tool.classpy].
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(build_app(), ["status"])
    assert result.exit_code == 0
    assert "Done" in result.output


def test_todo_lists_planned_classes_in_build_order(tmp_path):
    puml, src = _project(tmp_path)
    result = runner.invoke(
        build_app(), ["todo", "--puml", str(puml), "--src", str(src)]
    )
    assert result.exit_code == 0
    # Done is implemented; only the planned Missing is listed.
    assert "Missing" in result.output
    assert "1 class(es) to implement." in result.output


def test_todo_partial_flag_widens_the_scope(tmp_path):
    puml, src = _project(tmp_path)
    # Make Done partial by adding an unmet member; it should then show up too.
    puml.write_text(
        DIAGRAM.replace("class Done <<planned>> {\n    +run()", "class Done"
                        " <<planned>> {\n    +run()\n    +stop()"),
        encoding="utf-8",
    )
    result = runner.invoke(
        build_app(), ["todo", "--partial", "--puml", str(puml), "--src", str(src)]
    )
    assert result.exit_code == 0
    assert "Done" in result.output and "Missing" in result.output


def test_cli_flags_override_pyproject_config(tmp_path, monkeypatch):
    puml, src = _project(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.classpy]\npuml = "nonexistent.puml"\nsrc = "nowhere"\n',
        encoding="utf-8",
    )
    # Explicit flags must win over the (deliberately broken) config values.
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        build_app(), ["status", "--puml", str(puml), "--src", str(src)]
    )
    assert result.exit_code == 0
    assert "Done" in result.output
