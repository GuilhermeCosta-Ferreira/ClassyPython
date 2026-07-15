"""Discover classes and their members in a Python source tree using ``ast``.

For each class we collect:
  * **methods** — functions defined directly in the class body.
  * **attributes** — class-level assignments/annotations (including dataclass
    fields and Enum members) and ``self.<name> = ...`` assignments in any method.
"""

from __future__ import annotations

import ast
from pathlib import Path

from classpy.domain.models import CodeClass


class CodeInspector:
    """Walk a source root and return the classes it defines."""

    def inspect(self, root: str | Path) -> list[CodeClass]:
        """Return every :class:`CodeClass` found under ``root``."""
        root_path = Path(root)
        found: list[CodeClass] = []
        for file_path in sorted(root_path.rglob("*.py")):
            found.extend(self._inspect_file(file_path))
        return found

    def _inspect_file(self, file_path: Path) -> list[CodeClass]:
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            return []

        module_path = file_path.as_posix()
        classes: list[CodeClass] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                attributes, methods = self._extract_members(node)
                classes.append(
                    CodeClass(
                        name=node.name,
                        module_path=module_path,
                        attributes=attributes,
                        methods=methods,
                    )
                )
        return classes

    @staticmethod
    def _extract_members(node: ast.ClassDef) -> tuple[set[str], set[str]]:
        attributes: set[str] = set()
        methods: set[str] = set()

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.add(item.name)
                attributes.update(_self_assignments(item))
            elif isinstance(item, ast.Assign):
                attributes.update(
                    t.id for t in item.targets if isinstance(t, ast.Name)
                )
            elif isinstance(item, ast.AnnAssign) and isinstance(
                item.target, ast.Name
            ):
                attributes.add(item.target.id)

        return attributes, methods


def _self_assignments(func: ast.AST) -> set[str]:
    """Names assigned via ``self.<name> = ...`` anywhere inside ``func``."""
    names: set[str] = set()
    for sub in ast.walk(func):
        if isinstance(sub, ast.Assign):
            for target in sub.targets:
                if _is_self_attr(target):
                    names.add(target.attr)
        elif isinstance(sub, ast.AnnAssign) and _is_self_attr(sub.target):
            names.add(sub.target.attr)
    return names


def _is_self_attr(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )
