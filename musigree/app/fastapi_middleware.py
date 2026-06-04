from typing import Any

from fastapi import FastAPI


def add_app_middleware(app: FastAPI, middleware_class: type[Any], /, **kwargs: Any) -> None:
    """Register middleware; Starlette's ParamSpec typing does not match middleware classes."""
    app.add_middleware(middleware_class, **kwargs)  # type: ignore[arg-type]
