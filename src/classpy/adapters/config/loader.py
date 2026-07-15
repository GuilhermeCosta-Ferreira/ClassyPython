"""Load per-project defaults from a ``[tool.classpy]`` table in ``pyproject.toml``.

Precedence is resolved by the caller: an explicit CLI flag wins, otherwise the
value here, otherwise the CLI's hardcoded default. Any key may be absent; a missing
file or missing table yields an empty :class:`ClasspyConfig`.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ClasspyConfig:
    """Project defaults for the CLI. ``None`` means "not configured"."""

    puml: str | None = None
    src: str | None = None


class ConfigLoader:
    """Find and read the nearest ``pyproject.toml``'s ``[tool.classpy]`` table."""

    def __init__(self, filename: str = "pyproject.toml") -> None:
        self.filename = filename

    def find_config_file(self, start: str | Path | None = None) -> Path | None:
        """Walk up from ``start`` (default cwd) to the first ``pyproject.toml``."""
        origin = Path(start or Path.cwd()).resolve()
        for directory in (origin, *origin.parents):
            candidate = directory / self.filename
            if candidate.is_file():
                return candidate
        return None

    def load(self, start: str | Path | None = None) -> ClasspyConfig:
        """Return the config from the nearest ``pyproject.toml``, or empty."""
        path = self.find_config_file(start)
        if path is None:
            return ClasspyConfig()
        return self.load_file(path)

    def load_file(self, path: str | Path) -> ClasspyConfig:
        """Read the ``[tool.classpy]`` table out of a specific TOML file."""
        with open(path, "rb") as handle:
            data = tomllib.load(handle)
        table = data.get("tool", {}).get("classpy", {})
        return ClasspyConfig(puml=table.get("puml"), src=table.get("src"))
