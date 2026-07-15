"""Typer command-line interface for classpy."""

from __future__ import annotations

import typer

from classpy.domain.models import ImplementationStatus
from classpy.services.sync_service import SyncReport, SyncService

DEFAULT_PUML = "docs/class.puml"
DEFAULT_SRC = "src"

_LABELS = {
    ImplementationStatus.IMPLEMENTED: ("impl", "green"),
    ImplementationStatus.PARTIAL: ("part", "yellow"),
    ImplementationStatus.PLANNED: ("plan", "red"),
    ImplementationStatus.EXTERNAL: ("ext ", "blue"),
}

_PUML_OPTION = typer.Option(DEFAULT_PUML, "--puml", help="Path to the .puml diagram.")
_SRC_OPTION = typer.Option(DEFAULT_SRC, "--src", help="Source root to scan.")


class Cli:
    """Command handlers, kept in a class so they compose one service instance."""

    def __init__(self, service: SyncService | None = None) -> None:
        self.service = service or SyncService()

    def status(
        self,
        puml: str = _PUML_OPTION,
        src: str = _SRC_OPTION,
    ) -> None:
        """Report each class's implementation status without changing anything."""
        report = self.service.status(puml, src)
        _render(report, wrote=False)

    def sync(
        self,
        puml: str = _PUML_OPTION,
        src: str = _SRC_OPTION,
        check: bool = typer.Option(
            False,
            "--check",
            help="Do not write; exit non-zero if the diagram is out of date.",
        ),
    ) -> None:
        """Repaint the diagram so each class's colour matches the code."""
        if check:
            report = self.service.status(puml, src)
            _render(report, wrote=False)
            if report.is_stale:
                raise typer.Exit(code=1)
            return

        report = self.service.sync(puml, src)
        _render(report, wrote=True)


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


def build_app() -> typer.Typer:
    """Construct the Typer application with its commands registered."""
    app = typer.Typer(
        help="Keep a PlantUML class diagram in sync with the code.",
        no_args_is_help=True,
        add_completion=False,
    )
    cli = Cli()
    app.command()(cli.status)
    app.command()(cli.sync)
    return app


app = build_app()


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
