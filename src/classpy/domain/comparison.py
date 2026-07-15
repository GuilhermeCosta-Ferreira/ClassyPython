"""Decide a class's implementation status by matching declared members."""

from __future__ import annotations

from classpy.domain.models import (
    ClassComparison,
    CodeClass,
    ImplementationStatus,
    UmlClass,
)


class StatusComparator:
    """Compare a declared UML class against its (optional) code counterpart.

    Rules:
      * ``external`` UML classes are left untouched.
      * no matching code class -> ``planned``.
      * code class present but declared members missing -> ``partial``.
      * code class present with every declared member -> ``implemented``.
      * a UML class with no declared members can only be planned or implemented.
    """

    def compare(
        self, uml_class: UmlClass, code_class: CodeClass | None
    ) -> ClassComparison:
        if uml_class.stereotype == ImplementationStatus.EXTERNAL.stereotype:
            return ClassComparison(uml_class, ImplementationStatus.EXTERNAL, [])

        if code_class is None:
            return ClassComparison(
                uml_class, ImplementationStatus.PLANNED, list(uml_class.members)
            )

        present = code_class.member_names
        missing = [m for m in uml_class.members if m.name not in present]

        if missing:
            return ClassComparison(uml_class, ImplementationStatus.PARTIAL, missing)
        return ClassComparison(uml_class, ImplementationStatus.IMPLEMENTED, [])
