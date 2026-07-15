"""Rewrite class stereotypes in a PlantUML diagram, leaving all else intact.

Only the ``<<stereotype>>`` token on each ``class``/``enum`` declaration line is
touched; layout, members, comments and relationships are preserved byte-for-byte.
"""

from __future__ import annotations

import re
from pathlib import Path

from classpy.domain.models import ClassComparison

_DECL_RE = re.compile(
    r"^(?P<indent>\s*)"
    r"(?P<kw>(?:abstract\s+)?(?:class|enum|interface))\s+"
    r"(?P<name>\w+)"
    r"\s*(?P<stereo><<\s*\w+\s*>>)?"
    r"(?P<rest>.*)$"
)


class PumlWriter:
    """Apply computed statuses back onto diagram text."""

    def apply(self, text: str, comparisons: list[ClassComparison]) -> str:
        """Return ``text`` with each class's stereotype set from ``comparisons``."""
        target = {
            comparison.uml_class.name: comparison.status.stereotype
            for comparison in comparisons
        }
        newline = "\r\n" if "\r\n" in text else "\n"
        lines = text.splitlines()
        updated = [self._rewrite_line(line, target) for line in lines]
        result = newline.join(updated)
        if text.endswith(("\n", "\r")):
            result += newline
        return result

    def write_file(
        self, path: str | Path, comparisons: list[ClassComparison]
    ) -> None:
        """Rewrite the diagram at ``path`` in place."""
        file_path = Path(path)
        original = file_path.read_text(encoding="utf-8")
        file_path.write_text(self.apply(original, comparisons), encoding="utf-8")

    @staticmethod
    def _rewrite_line(line: str, target: dict[str, str]) -> str:
        match = _DECL_RE.match(line)
        if match is None or match.group("name") not in target:
            return line

        stereotype = f"<<{target[match.group('name')]}>>"
        rest = match.group("rest")
        if rest and not rest.startswith(" "):
            rest = " " + rest
        return f"{match.group('indent')}{match.group('kw')} " \
               f"{match.group('name')} {stereotype}{rest}"
