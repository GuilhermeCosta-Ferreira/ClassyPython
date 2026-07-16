"""Typer command-line interface for classpy."""

from __future__ import annotations

import typer

from classpy.adapters.config.loader import ConfigLoader
from classpy.domain.models import ImplementationStatus
from classpy.services.sync_service import PendingReport, SyncReport, SyncService

DEFAULT_PUML = "docs/class.puml"
DEFAULT_SRC = "src"

_PUML_HELP = (
    "Path to the .puml diagram. "
    f"Defaults to [tool.classpy] puml, then {DEFAULT_PUML}."
)
_SRC_HELP = f"Source root to scan. Defaults to [tool.classpy] src, then {DEFAULT_SRC}."

_LABELS = {
    ImplementationStatus.IMPLEMENTED: ("impl", "green"),
    ImplementationStatus.PARTIAL: ("part", "yellow"),
    ImplementationStatus.PLANNED: ("plan", "red"),
    ImplementationStatus.EXTERNAL: ("ext ", "blue"),
}

_PUML_OPTION = typer.Option(None, "--puml", help=_PUML_HELP)
_SRC_OPTION = typer.Option(None, "--src", help=_SRC_HELP)


class Cli:
    """Command handlers, kept in a class so they compose one service instance."""

    def __init__(
        self,
        service: SyncService | None = None,
        config_loader: ConfigLoader | None = None,
    ) -> None:
        self.service = service or SyncService()
        self.config_loader = config_loader or ConfigLoader()

    def _resolve(self, puml: str | None, src: str | None) -> tuple[str, str]:
        """Apply precedence: CLI flag > pyproject [tool.classpy] > hardcoded default."""
        config = self.config_loader.load()
        return (
            puml or config.puml or DEFAULT_PUML,
            src or config.src or DEFAULT_SRC,
        )

    def init(
        self,
        puml: str | None = _PUML_OPTION,
        src: str | None = _SRC_OPTION,
    ) -> None:
        """Scaffold an empty class diagram, creating its folder if needed."""
        puml, _ = self._resolve(puml, src)
        created = self.service.init(puml)
        if created:
            typer.echo(f"Created {puml}")
        else:
            typer.echo(f"{puml} already exists — leaving it untouched.")

    def status(
        self,
        puml: str | None = _PUML_OPTION,
        src: str | None = _SRC_OPTION,
    ) -> None:
        """Report each class's implementation status without changing anything."""
        puml, src = self._resolve(puml, src)
        report = self.service.status(puml, src)
        _render(report, wrote=False)

    def sync(
        self,
        puml: str | None = _PUML_OPTION,
        src: str | None = _SRC_OPTION,
        check: bool = typer.Option(
            False,
            "--check",
            help="Do not write; exit non-zero if the diagram is out of date.",
        ),
    ) -> None:
        """Repaint the diagram so each class's colour matches the code."""
        puml, src = self._resolve(puml, src)
        if check:
            report = self.service.status(puml, src)
            _render(report, wrote=False)
            if report.is_stale:
                raise typer.Exit(code=1)
            return

        report = self.service.sync(puml, src)
        _render(report, wrote=True)

    def todo(
        self,
        puml: str | None = _PUML_OPTION,
        src: str | None = _SRC_OPTION,
        partial: bool = typer.Option(
            False,
            "--partial",
            help="Also list partially-implemented classes (default: only planned).",
        ),
    ) -> None:
        """List unimplemented classes in build order, least-dependent first."""
        puml, src = self._resolve(puml, src)
        report = self.service.pending(puml, src, include_partial=partial)
        _render_pending(report)


def _render(report: SyncReport, wrote: bool) -> None:
    changed = {id(c) for c in report.changed}
    for comparison in report.comparisons:
        label, colour = _LABELS[comparison.status]
        mark = "*" if id(comparison) in changed else " "
        badge = typer.style(f"[{label}]", fg=colour)
        typer.echo(f" {mark} {badge} {comparison.uml_class.name}")

    counts = report.counts
    typer.echo("")
    typer.echo(
        "impl={impl}  part={part}  plan={plan}  ext={ext}".format(
            impl=counts[ImplementationStatus.IMPLEMENTED],
            part=counts[ImplementationStatus.PARTIAL],
            plan=counts[ImplementationStatus.PLANNED],
            ext=counts[ImplementationStatus.EXTERNAL],
        )
    )

    if wrote:
        if report.changed:
            typer.echo(f"Repainted {len(report.changed)} class(es).")
        else:
            typer.echo("Diagram already up to date.")
    elif report.is_stale:
        typer.echo(f"{len(report.changed)} class(es) out of date.")
    else:
        typer.echo("Diagram already up to date.")


def _render_pending(report: PendingReport) -> None:
    if report.is_empty:
        scope = "planned or partial" if report.include_partial else "planned"
        typer.echo(f"Nothing to implement — no {scope} classes.")
        return

    typer.echo("Build order (least-dependent first):")
    typer.echo("")
    width = len(str(len(report.ordered)))
    for index, item in enumerate(report.ordered, start=1):
        comparison = item.comparison
        label, colour = _LABELS[comparison.status]
        badge = typer.style(f"[{label}]", fg=colour)
        line = f" {index:>{width}}. {badge} {comparison.uml_class.name}"
        if item.depends_on:
            line += typer.style(
                f"  (needs {', '.join(item.depends_on)})", fg="bright_black"
            )
        typer.echo(line)

    typer.echo("")
    typer.echo(f"{len(report.ordered)} class(es) to implement.")


def build_app() -> typer.Typer:
    """Construct the Typer application with its commands registered."""
    app = typer.Typer(
        help="Keep a PlantUML class diagram in sync with the code.",
        no_args_is_help=True,
        add_completion=False,
    )
    cli = Cli()
    app.command()(cli.init)
    app.command()(cli.status)
    app.command()(cli.sync)
    app.command()(cli.todo)
    return app


app = build_app()


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
