"""Class-based routing with controllers and dependency injection for FastAPI."""

from .controller import (
    APIController,
    add_controller,
    add_controllers,
    controller,
    delete,
    get,
    patch,
    post,
    put,
    reset_controllers,
)
from .di import inject

__all__ = [
    "APIController",
    "add_controller",
    "add_controllers",
    "controller",
    "delete",
    "get",
    "inject",
    "patch",
    "post",
    "put",
    "reset_controllers",
]
