"""Tests for the global controller registry and endpoint variants."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_control import (
    APIController,
    add_controller,
    add_controllers,
    controller,
    get,
    reset_controllers,
)
from fastapi_control.controller import __controllers__


def test_reset_controllers_clears_the_registry() -> None:
    assert __controllers__

    reset_controllers()

    assert __controllers__ == []

    # re-register something so later add_controllers calls keep working
    _register_simple_controller()


def _register_simple_controller() -> None:
    @controller(prefix="/registry")
    class RegistryController(APIController):
        @get(path="/ping")
        def ping(self) -> dict[str, str]:
            return {"pong": "true"}


def test_add_controllers_mounts_every_registered_controller() -> None:
    reset_controllers()
    _register_simple_controller()

    api = FastAPI()
    add_controllers(api)
    client = TestClient(api)

    assert client.get("/registry/ping").json() == {"pong": "true"}


def test_add_controller_to_two_apps() -> None:
    @controller(prefix="/shared")
    class SharedController(APIController):
        @get(path="/hello")
        def hello(self) -> dict[str, str]:
            return {"hello": "world"}

    first_api = FastAPI()
    second_api = FastAPI()
    add_controller(first_api, SharedController)
    add_controller(second_api, SharedController)

    first_response = TestClient(first_api).get("/shared/hello")
    second_response = TestClient(second_api).get("/shared/hello")
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json() == {"hello": "world"}


def test_staticmethod_endpoints_are_registered_without_injection() -> None:
    @controller(prefix="/static")
    class StaticController(APIController):
        @staticmethod
        @get(path="/health")
        def health() -> dict[str, str]:
            return {"status": "ok"}

        @staticmethod
        @get(path="/add")
        def add(a: int, b: int) -> int:
            return a + b

    api = FastAPI()
    add_controller(api, StaticController)
    client = TestClient(api)

    assert client.get("/static/health").json() == {"status": "ok"}
    assert client.get("/static/add", params={"a": 2, "b": 3}).json() == 5


def test_endpoint_without_self_is_registered_without_injection() -> None:
    @controller(prefix="/noself")
    class NoSelfController(APIController):
        @get(path="/version")
        def version() -> dict[str, str]:
            return {"version": "0.5.0"}

    api = FastAPI()
    add_controller(api, NoSelfController)
    client = TestClient(api)

    assert client.get("/noself/version").json() == {"version": "0.5.0"}


def test_controller_instance_is_created_per_request() -> None:
    instantiations = {"count": 0}

    @controller(prefix="/per-request")
    class PerRequestController(APIController):
        def __init__(self) -> None:
            instantiations["count"] += 1

        @get(path="/call")
        def call(self) -> dict[str, int]:
            return {"count": instantiations["count"]}

    api = FastAPI()
    add_controller(api, PerRequestController)
    client = TestClient(api)

    assert client.get("/per-request/call").status_code == 200
    assert client.get("/per-request/call").status_code == 200
    assert instantiations["count"] == 2
