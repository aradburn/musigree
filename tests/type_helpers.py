"""Typing helpers for tests."""


def as_object(value: object) -> object:
    """Return ``value`` typed as ``object``.

    Tests compare Luigi parameters, middleware classes, and similar values
    with objects outside their declared types. A ``cast`` to ``object`` or
    ``Any`` is reported as unnecessary when the checker already uses that type.
    """
    return value
