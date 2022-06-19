from typing import Any, Callable, Optional, Type, TypeVar, Union

from kink import Container
from kink import inject as kink_inject

T = TypeVar("T")
S = TypeVar("S")

ServiceDefinition = Union[Type[S], Callable]
ServiceResult = Union[S, Callable]


class _Container(Container):
    """
    This is a hack to combine the alias and the use_factory params
    because in the kink default Container class when alias param
    is used, the use_factory param is ignored.
    """

    def __getitem__(self, key: Union[str, Type]) -> Any:
        if key in self._aliases:
            key = self._aliases[key][0]

        return Container.__getitem__(self, key)


_di = _Container()


def inject(alias: Optional[Type[Any]] = None) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        wrapper = (
            kink_inject(use_factory=True, container=_di)
            if alias is None
            else kink_inject(alias=alias, use_factory=True, container=_di)
        )
        return wrapper(cls)  # type: ignore

    return decorator


def factory(f: Callable[..., T]) -> Callable[[], T]:
    return lambda: f()


def instantiate(f: Callable[..., T]) -> T:
    return f()
