"""Order pending classes least-dependent first, to guide build order."""

from __future__ import annotations

from classpy.domain.models import ClassComparison, OrderedClass, UmlRelationship


class DependencyOrderer:
    """Sort a set of pending classes into a sensible implementation order.

    The ordering is a layered topological sort over the dependencies *within
    the pending set* — dependencies on already-implemented classes are ignored
    because they are done and never block. Leaves (classes depending on nothing
    still to build) come first; within a layer, classes are ordered by their
    dependency count and then name for a stable result. A dependency cycle is
    broken by emitting the class with the fewest unresolved dependencies.
    """

    def order(
        self,
        pending: list[ClassComparison],
        relationships: list[UmlRelationship],
    ) -> list[OrderedClass]:
        scope = {c.uml_class.name for c in pending}
        by_name = {c.uml_class.name: c for c in pending}
        deps: dict[str, set[str]] = {name: set() for name in scope}
        for rel in relationships:
            if rel.source in scope and rel.target in scope:
                deps[rel.source].add(rel.target)

        ordered: list[OrderedClass] = []
        emitted: set[str] = set()
        remaining = set(scope)
        while remaining:
            ready = [n for n in remaining if deps[n] <= emitted]
            if ready:
                batch = sorted(ready, key=lambda n: (len(deps[n]), n))
            else:  # cycle — break on the least-blocked class
                batch = [min(remaining, key=lambda n: (len(deps[n] - emitted), n))]
            for name in batch:
                ordered.append(
                    OrderedClass(
                        comparison=by_name[name],
                        depends_on=sorted(deps[name]),
                    )
                )
                emitted.add(name)
                remaining.discard(name)
        return ordered
