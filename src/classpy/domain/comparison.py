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
      * code class present with every declared member, but some method is only a
        stub (``pass`` / ``...`` / ``raise NotImplementedError``) -> ``partial``.
        This holds whether or not the stub method is one of the declared members.
      * code class present with every declared member and no stub methods
        -> ``implemented``.

    The stub rule is **ignored for abstract classes** — those declared
    ``abstract``/``interface`` in the UML, or backed by an ``ABC``/``Protocol``
    (or ``@abstractmethod``) in the code — because stub method bodies are their
    whole point. Such a class is ``implemented`` once all members are present.
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
        is_abstract = uml_class.is_abstract or code_class.is_abstract
        if code_class.has_stub and not is_abstract:
            return ClassComparison(uml_class, ImplementationStatus.PARTIAL, [])
        return ClassComparison(uml_class, ImplementationStatus.IMPLEMENTED, [])
