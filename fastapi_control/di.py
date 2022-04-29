from typing import Any, Callable, Optional, Type, TypeVar

import kink

T = TypeVar("T")


def inject(alias: Optional[Type[Any]] = None) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        wrapper = (
            kink.inject(use_factory=True)
            if alias is None
            else kink.inject(alias=alias, use_factory=True)
        )
        return wrapper(cls)

    return decorator


def factory(f: Callable[..., T]) -> Callable[[], T]:
    return lambda: f()


def instantiate(f: Callable[..., T]) -> T:
    return f()
