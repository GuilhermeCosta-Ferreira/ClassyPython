"""Scaffold a fresh PlantUML class diagram from an empty layered template.

The template mirrors ``docs/class.puml``'s skin — the three layer packages with
their fill colours, the status legend and the stereotype tags — but carries no
classes. It is the starting point ``classpy init`` writes into a new project.
"""

from __future__ import annotations

from pathlib import Path

EMPTY_TEMPLATE = """\
@startuml
left to right direction
skinparam linetype ortho
skinparam class {
    BackgroundColor<<implemented>> #D5F5D5
    BorderColor<<implemented>> #2E7D32
    FontColor<<implemented>> #1B5E20

    BackgroundColor<<partial>> #FFF3CD
    BorderColor<<partial>> #B8860B
    FontColor<<partial>> #7A5600

    BackgroundColor<<planned>> #F8D7DA
    BorderColor<<planned>> #B02A37
    FontColor<<planned>> #842029

    BackgroundColor<<external>> #E3F2FD
    BorderColor<<external>> #1565C0
    FontColor<<external>> #0D47A1
}

legend right
|= Colour |
|<#D5F5D5> Implemented |
|<#FFF3CD> Partially implemented |
|<#F8D7DA> Planned / not implemented |
|<#E3F2FD> External dependency |
endlegend

' 0 = hide dependency lines
' 1 = show dependency lines
!$SHOW_DEPENDENCIES = 0


'=============================================================================='
'Service Layer'
'=============================================================================='
package "Service Layer" #E8F5E9 {
}


'=============================================================================='
'Model Domain'
'=============================================================================='
package "Model Domain Layer" #FFF8E1 {
}


'=============================================================================='
'Adapter Layer'
'=============================================================================='
package "Adapter Layer" #E3F2FD {
}

@enduml
"""


class PumlScaffold:
    """Write a starter diagram containing only the layered scaffold."""

    def __init__(self, template: str = EMPTY_TEMPLATE) -> None:
        self.template = template

    def create_file(self, path: str | Path) -> bool:
        """Write the template to ``path``, creating parent folders as needed.

        Return ``True`` when the file was created, ``False`` when it already
        existed (in which case it is left untouched).
        """
        file_path = Path(path)
        if file_path.exists():
            return False
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.template, encoding="utf-8")
        return True
