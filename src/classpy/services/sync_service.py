"""Orchestrate the diagram-to-code synchronisation use case."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from classpy.adapters.code.inspector import CodeInspector
from classpy.adapters.puml.parser import PumlParser
from classpy.adapters.puml.writer import PumlWriter
from classpy.domain.comparison import StatusComparator
from classpy.domain.locator import ClassLocator
from classpy.domain.models import ClassComparison, ImplementationStatus


@dataclass
class SyncReport:
    """Result of a status/sync run over one diagram."""

    comparisons: list[ClassComparison] = field(default_factory=list)

    @property
    def changed(self) -> list[ClassComparison]:
        """Classes whose stereotype differs from what the code implies."""
        return [
            c
            for c in self.comparisons
            if c.uml_class.stereotype != c.status.stereotype
        ]

    @property
    def is_stale(self) -> bool:
        """True when at least one class would be repainted."""
        return bool(self.changed)

    @property
    def counts(self) -> dict[ImplementationStatus, int]:
        """Number of classes resolved to each status."""
        tally = Counter(c.status for c in self.comparisons)
        return {status: tally.get(status, 0) for status in ImplementationStatus}


class SyncService:
    """Wire the parser, inspector, comparator, locator and writer together."""

    def __init__(
        self,
        parser: PumlParser | None = None,
        inspector: CodeInspector | None = None,
        comparator: StatusComparator | None = None,
        locator: ClassLocator | None = None,
        writer: PumlWriter | None = None,
    ) -> None:
        self.parser = parser or PumlParser()
        self.inspector = inspector or CodeInspector()
        self.comparator = comparator or StatusComparator()
        self.locator = locator or ClassLocator()
        self.writer = writer or PumlWriter()

    def status(self, puml_path: str | Path, source_root: str | Path) -> SyncReport:
        """Compute each class's status without modifying the diagram."""
        uml_classes = self.parser.parse_file(puml_path)
        code_classes = self.inspector.inspect(source_root)

        comparisons = [
            self.comparator.compare(uml, self.locator.select(uml, code_classes))
            for uml in uml_classes
        ]
        return SyncReport(comparisons=comparisons)

    def sync(self, puml_path: str | Path, source_root: str | Path) -> SyncReport:
        """Compute statuses and write the repainted diagram back to disk."""
        report = self.status(puml_path, source_root)
        if report.is_stale:
            self.writer.write_file(puml_path, report.comparisons)
        return report
