"""Typed construction helper for Luigi tasks.

Luigi declares ``py.typed`` but ``Task.__init__`` has no annotations. A task
class that does not define ``__init__`` is therefore an untyped call under
``mypy --strict``. This mixin supplies a typed constructor and forwards to
Luigi's implementation.
"""

from typing import Any, cast

import luigi


class TypedLuigiInit:
    """Give a Luigi task subclass a typed ``__init__``."""

    # noinspection invalid-cast
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        luigi.Task.__init__(cast("luigi.Task", self), *args, **kwargs)
