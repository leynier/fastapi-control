"""Dependency injection support built on top of kink."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from kink import Container
from kink import inject as kink_inject

T = TypeVar("T")

_di = Container()  # type: ignore[no-untyped-call]


def inject(alias: type[Any] | None = None) -> Callable[[type[T]], type[T]]:
    """Class decorator that makes the decorated class injectable.

    The constructor arguments of the decorated class are resolved from the
    global service container when it is instantiated. When ``alias`` is
    provided, the class is also registered as the default implementation of
    that abstraction, so dependents can depend on the abstraction instead.
    """

    def decorator(cls: type[T]) -> type[T]:
        wrapper = (
            kink_inject(use_factory=True, container=_di)
            if alias is None
            else kink_inject(alias=alias, use_factory=True, container=_di)
        )
        return wrapper(cls)  # type: ignore[return-value]

    return decorator


def factory(f: Callable[..., T]) -> Callable[[], T]:
    """Adapt ``f`` into a parameterless factory suitable for ``Depends``."""

    def _factory() -> T:
        return f()

    return _factory


def instantiate(f: Callable[..., T]) -> T:
    """Call the given factory and return a fresh instance."""
    return f()
