"""Map a UML class onto the code class that implements it.

Matching is by class name plus the ``PascalCase`` -> ``snake_case`` file-naming
convention (``SimulationRun`` -> ``simulation_run.py``). The UML package hierarchy
is used to disambiguate when several classes share a name.
"""

from __future__ import annotations

import re

from classpy.domain.models import CodeClass, UmlClass

_CAMEL_BOUNDARY_1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_BOUNDARY_2 = re.compile(r"([a-z0-9])([A-Z])")
_NON_WORD = re.compile(r"[^0-9a-zA-Z]+")


class ClassLocator:
    """Resolve which :class:`CodeClass` (if any) implements a given UML class."""

    def to_snake_case(self, name: str) -> str:
        """Convert a ``PascalCase``/``camelCase`` name to ``snake_case``.

        Handles acronym runs: ``HTTPClient`` -> ``http_client``,
        ``PumlParser`` -> ``puml_parser``.
        """
        stage_1 = _CAMEL_BOUNDARY_1.sub(r"\1_\2", name)
        stage_2 = _CAMEL_BOUNDARY_2.sub(r"\1_\2", stage_1)
        return stage_2.lower()

    def expected_module(self, uml_class: UmlClass) -> str:
        """The file name the class is expected to live in, e.g. ``uml_class.py``."""
        return f"{self.to_snake_case(uml_class.name)}.py"

    def select(
        self, uml_class: UmlClass, code_classes: list[CodeClass]
    ) -> CodeClass | None:
        """Pick the best code match for ``uml_class`` from ``code_classes``.

        Preference order: correct file name, then a package-path hint, then any
        class sharing the name.
        """
        named = [c for c in code_classes if c.name == uml_class.name]
        if not named:
            return None
        if len(named) == 1:
            return named[0]

        expected = self.expected_module(uml_class)
        by_file = [c for c in named if self._basename(c.module_path) == expected]
        pool = by_file or named

        hinted = [c for c in pool if self._package_matches(uml_class, c)]
        return (hinted or pool)[0]

    def _package_matches(self, uml_class: UmlClass, code_class: CodeClass) -> bool:
        path_parts = self._path_parts(code_class.module_path)
        for segment in uml_class.package.split("/"):
            token = self.to_snake_case(_NON_WORD.sub("_", segment).strip("_"))
            if token and token in path_parts:
                return True
        return False

    @staticmethod
    def _basename(module_path: str) -> str:
        return module_path.replace("\\", "/").rsplit("/", 1)[-1]

    @staticmethod
    def _path_parts(module_path: str) -> set[str]:
        normalized = module_path.replace("\\", "/")
        return {part for part in normalized.split("/") if part}
