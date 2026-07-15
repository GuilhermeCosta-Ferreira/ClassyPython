"""Tests for the pyproject.toml [tool.classpy] config loader."""

from textwrap import dedent

from classpy.adapters.config.loader import ClasspyConfig, ConfigLoader


def _write(path, body):
    path.write_text(dedent(body).strip() + "\n", encoding="utf-8")


def test_reads_puml_and_src(tmp_path):
    _write(
        tmp_path / "pyproject.toml",
        """
        [tool.classpy]
        puml = "docs/architecture.puml"
        src = "app"
        """,
    )
    config = ConfigLoader().load(start=tmp_path)
    assert config == ClasspyConfig(puml="docs/architecture.puml", src="app")


def test_missing_table_yields_empty_config(tmp_path):
    _write(tmp_path / "pyproject.toml", "[tool.black]\nline-length = 88")
    assert ConfigLoader().load(start=tmp_path) == ClasspyConfig()


def test_partial_table_leaves_other_key_none(tmp_path):
    _write(tmp_path / "pyproject.toml", '[tool.classpy]\nsrc = "app"')
    config = ConfigLoader().load(start=tmp_path)
    assert config == ClasspyConfig(puml=None, src="app")


def test_walks_up_to_nearest_pyproject(tmp_path):
    _write(
        tmp_path / "pyproject.toml",
        '[tool.classpy]\npuml = "top.puml"\nsrc = "lib"',
    )
    nested = tmp_path / "packages" / "core"
    nested.mkdir(parents=True)
    config = ConfigLoader().load(start=nested)
    assert config == ClasspyConfig(puml="top.puml", src="lib")
