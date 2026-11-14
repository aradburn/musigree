def release_years(releases: dict[str, int | None]) -> dict[str, int | None]:
    """Widen a release-id map so it matches the relation field.

    A dict literal is inferred with ``Literal`` keys. ``dict`` is invariant,
    so that literal is not a ``dict[str, int | None]`` when the destination
    is the union ``dict[str, int | None] | None``.
    """
    return releases
