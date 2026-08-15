"""Tests for the dependency injection layer (kink integration)."""

from kink import Container
from kink import inject as kink_inject

from fastapi_control import inject


def test_kink_container_supports_alias_with_factory() -> None:
    """Regression test: kink's Container must natively combine alias and
    use_factory, which is what allowed removing the _Container workaround."""
    container = Container()

    class Abstraction:
        def value(self) -> str:
            raise NotImplementedError

    @kink_inject(alias=Abstraction, use_factory=True, container=container)
    class Implementation(Abstraction):
        def value(self) -> str:
            return "impl"

    # resolution by concrete class hits the factory (fresh instance each time)
    first = container[Implementation]
    second = container[Implementation]
    assert isinstance(first, Implementation)
    assert first is not second
    assert first.value() == "impl"

    # resolution by alias must also hit the factory, not a stale singleton
    third = container[Abstraction]
    fourth = container[Abstraction]
    assert isinstance(third, Implementation)
    assert third is not fourth


def test_inject_with_alias_resolves_implementation() -> None:
    class ServiceAbstraction:
        def value(self) -> str:
            raise NotImplementedError

    @inject(alias=ServiceAbstraction)
    class ServiceImplementation(ServiceAbstraction):
        def value(self) -> str:
            return "service"

    @inject()
    class Dependent:
        def __init__(self, service: ServiceAbstraction) -> None:
            self.service = service

    dependent = Dependent()
    assert isinstance(dependent.service, ServiceImplementation)
    assert dependent.service.value() == "service"


def test_nested_injection() -> None:
    """Mirrors the nested greeters of example/main.py."""

    @inject()
    class Inner:
        def value(self) -> str:
            return "inner"

    @inject()
    class Middle:
        def __init__(self, inner: Inner) -> None:
            self.inner = inner

        def value(self) -> str:
            return f"middle({self.inner.value()})"

    @inject()
    class Outer:
        def __init__(self, middle: Middle) -> None:
            self.middle = middle

        def value(self) -> str:
            return f"outer({self.middle.value()})"

    assert Outer().value() == "outer(middle(inner))"


def test_injected_services_are_not_cached_across_resolutions() -> None:
    counter = {"count": 0}

    @inject()
    class CountingService:
        def __init__(self) -> None:
            counter["count"] += 1

    CountingService()
    CountingService()
    assert counter["count"] == 2
