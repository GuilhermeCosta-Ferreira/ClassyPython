"""Order pending classes least-dependent first, to guide build order."""

from __future__ import annotations

from classpy.domain.models import ClassComparison, OrderedClass, UmlRelationship


class DependencyOrderer:
    """Sort a set of pending classes into a sensible implementation order.

    The ordering is a layered topological sort over the dependencies *within
    the pending set*. A dependency that hops through an out-of-scope class (an
    interface that is only ``partial``, say) still links the two pending classes
    it sits between: out-of-scope nodes are collapsed transitively rather than
    severing the chain, so a realization of a not-yet-finished interface is not
    mistaken for a leaf. A terminal out-of-scope class (one already implemented,
    depending on nothing pending) collapses to nothing and never blocks. Leaves
    come first; within a layer, classes are ordered by their dependency count
    and then name for a stable result. A dependency cycle is broken by emitting
    the class with the fewest unresolved dependencies.
    """

    def order(
        self,
        pending: list[ClassComparison],
        relationships: list[UmlRelationship],
    ) -> list[OrderedClass]:
        scope = {c.uml_class.name for c in pending}
        by_name = {c.uml_class.name: c for c in pending}
        deps = self._pending_dependencies(scope, relationships)

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

    @staticmethod
    def _pending_dependencies(
        scope: set[str],
        relationships: list[UmlRelationship],
    ) -> dict[str, set[str]]:
        """Map each pending class to the pending classes it depends on.

        The full ``source -> target`` graph is walked so out-of-scope classes on
        a path are collapsed: the walk stops at each in-scope class it reaches
        (that class carries its own onward dependencies) and steps *through* any
        out-of-scope class, preserving transitive links that would otherwise be
        cut when an intermediate class is not part of the pending set.
        """
        graph: dict[str, set[str]] = {}
        for rel in relationships:
            graph.setdefault(rel.source, set()).add(rel.target)

        deps: dict[str, set[str]] = {}
        for name in scope:
            reachable: set[str] = set()
            seen: set[str] = set()
            stack = list(graph.get(name, ()))
            while stack:
                node = stack.pop()
                if node == name or node in seen:
                    continue
                seen.add(node)
                if node in scope:
                    reachable.add(node)  # in-scope dep; owns its onward deps
                else:
                    stack.extend(graph.get(node, ()))  # collapse: hop through
            deps[name] = reachable
        return deps
