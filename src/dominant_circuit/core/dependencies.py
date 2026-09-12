"""Shared deterministic transitive invalidation for decision and investigation records."""


def dependency_closure(changed, dependencies):
    affected = set(changed)
    while True:
        expanded = affected | {
            key for key, deps in dependencies.items() if affected.intersection(deps)
        }
        if expanded == affected:
            return affected
        affected = expanded
