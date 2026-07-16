"""Compute the UML-vs-code member-count balance for a set of classes."""

from __future__ import annotations

from enum import Enum

from classpy.domain.models import BalanceEntry, CodeClass, UmlClass


class SortMode(Enum):
    """How to order the balance rows."""

    ABS = "abs"
    """By absolute difference, largest gap first (the default)."""

    SIGNED = "signed"
    """By signed difference: UML>code first, then UML=code, then UML<code."""


def _is_private(name: str) -> bool:
    """True for a member whose name is prefixed with an underscore."""
    return name.startswith("_")


class BalanceCalculator:
    """Turn (UML class, matched code class) pairs into ordered balance rows.

    The UML count is the number of declared members. The code count is the
    number of attributes and methods on the matched class; underscore-prefixed
    (private) members are excluded unless ``count_private`` is set. The private
    toggle only affects the code side — the UML rarely declares private names.
    """

    def calculate(
        self,
        pairs: list[tuple[UmlClass, CodeClass | None]],
        count_private: bool = False,
        sort: SortMode = SortMode.ABS,
    ) -> list[BalanceEntry]:
        """Return one :class:`BalanceEntry` per pair, ordered by ``sort``."""
        entries = [
            BalanceEntry(
                name=uml.name,
                uml_count=len(uml.members),
                code_count=self._code_count(code, count_private),
            )
            for uml, code in pairs
        ]
        return self._sort(entries, sort)

    @staticmethod
    def _code_count(code: CodeClass | None, count_private: bool) -> int:
        if code is None:
            return 0
        names = code.member_names
        if not count_private:
            names = {n for n in names if not _is_private(n)}
        return len(names)

    @staticmethod
    def _sort(entries: list[BalanceEntry], sort: SortMode) -> list[BalanceEntry]:
        if sort is SortMode.SIGNED:
            return sorted(entries, key=lambda e: (-e.diff, e.name))
        return sorted(entries, key=lambda e: (-abs(e.diff), -e.diff, e.name))
