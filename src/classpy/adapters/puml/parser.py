"""Parse a PlantUML class diagram into :class:`UmlClass` domain objects.

A small line-oriented state machine: it tracks the stack of enclosing
``package "..." { }`` blocks and, inside a ``class``/``enum`` body, collects the
declared attributes and methods. Everything else (skinparam, legend,
relationships, comments, preprocessor directives) is ignored.
"""

from __future__ import annotations

import re
from pathlib import Path

from classpy.domain.models import MemberKind, UmlClass, UmlMember, UmlRelationship

_PACKAGE_RE = re.compile(r'^\s*package\s+(?:"([^"]*)"|(\S+))\s*\{\s*$')
_CLASS_RE = re.compile(
    r"^\s*(abstract\s+)?(class|enum|interface)\s+(\w+)\s*"
    r"(?:<<\s*(\w+)\s*>>)?\s*(\{)?\s*$"
)
_VISIBILITY = "+-#~"
_MODIFIERS = ("{static}", "{abstract}", "{field}", "{method}")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$")

# A relationship line: <lhs> <connector> <rhs> [: label]. The connector is a
# run of dashes/dots (the line) with optional single arrowheads on either end
# (``>`` ``|>`` ``<`` ``<|`` ``*`` ``o``). Optional "..." multiplicities and a
# trailing ``: label`` are tolerated and ignored.
_RELATION_RE = re.compile(
    r"""^\s*
        (?P<src>\w+)
        \s*(?:"[^"]*")?\s*
        (?P<arrow>(?:<\||<|\*|o)?[-.]+(?:\|>|>|\*|o)?)
        \s*(?:"[^"]*")?\s*
        (?P<dst>\w+)
        \s*(?::.*)?$
    """,
    re.VERBOSE,
)


class PumlParser:
    """Turn PlantUML text into the classes it declares."""

    def parse_file(self, path: str | Path) -> list[UmlClass]:
        """Parse the diagram stored at ``path``."""
        return self.parse(Path(path).read_text(encoding="utf-8"))

    def parse(self, text: str) -> list[UmlClass]:
        """Parse diagram ``text`` into a list of :class:`UmlClass`."""
        classes: list[UmlClass] = []
        package_stack: list[str] = []
        current: UmlClass | None = None

        for raw_line in text.splitlines():
            if current is not None:
                if self._is_block_close(raw_line):
                    classes.append(current)
                    current = None
                    continue
                member = self._parse_member(raw_line)
                if member is not None:
                    current.members.append(member)
                continue

            package_match = _PACKAGE_RE.match(raw_line)
            if package_match:
                package_stack.append(package_match.group(1) or package_match.group(2))
                continue

            class_match = _CLASS_RE.match(raw_line)
            if class_match:
                keyword = class_match.group(2)
                new_class = UmlClass(
                    name=class_match.group(3),
                    package="/".join(package_stack),
                    stereotype=(class_match.group(4) or "").lower(),
                    is_abstract=bool(class_match.group(1)) or keyword == "interface",
                )
                if class_match.group(5):  # opening brace -> has a body
                    current = new_class
                else:
                    classes.append(new_class)
                continue

            if self._is_block_close(raw_line) and package_stack:
                package_stack.pop()

        return classes

    def parse_relationships_file(self, path: str | Path) -> list[UmlRelationship]:
        """Parse the relationships declared in the diagram stored at ``path``."""
        return self.parse_relationships(Path(path).read_text(encoding="utf-8"))

    def parse_relationships(self, text: str) -> list[UmlRelationship]:
        """Extract directed dependencies from diagram ``text``.

        Each returned :class:`UmlRelationship` points ``source`` -> ``target``,
        meaning *source depends on target*. Arrowhead direction is normalised:
        a left head (``<``/``<|``) or a left-side ``*``/``o`` owner flips the
        edge so the dependent class is always ``source``. Lines that are class
        or package declarations are skipped.
        """
        relationships: list[UmlRelationship] = []
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith(("'", "!")):
                continue
            if _CLASS_RE.match(raw_line) or _PACKAGE_RE.match(raw_line):
                continue
            match = _RELATION_RE.match(raw_line)
            if match is None:
                continue
            src, dst = match.group("src"), match.group("dst")
            arrow = match.group("arrow")
            # Normalise so `source` is the dependent side. A left arrowhead
            # (`<`/`<|`) or a right-side composition/aggregation owner (`*`/`o`)
            # means the real dependent is on the right, so flip the edge.
            if arrow[0] == "<" or arrow[-1] in "*o":
                src, dst = dst, src
            if src != dst:
                relationships.append(UmlRelationship(source=src, target=dst))
        return relationships

    @staticmethod
    def _is_block_close(line: str) -> bool:
        return line.strip() == "}"

    @staticmethod
    def _parse_member(line: str) -> UmlMember | None:
        text = line.strip()
        if not text or text.startswith("'") or text.startswith("!"):
            return None
        if text[0] in _VISIBILITY:
            text = text[1:].strip()
        for modifier in _MODIFIERS:
            text = text.replace(modifier, "")
        text = text.strip()
        if "{" in text or "}" in text:
            return None

        if "(" in text:
            name = text.split("(", 1)[0].strip()
            kind = MemberKind.METHOD
        else:
            name = text.split(":", 1)[0].strip()
            kind = MemberKind.ATTRIBUTE

        if not _IDENTIFIER_RE.match(name):
            return None
        return UmlMember(name=name, kind=kind)
