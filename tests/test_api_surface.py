"""Tests covering the remaining public decorators and helpers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_control import (
    APIController,
    add_controller,
    controller,
    delete,
    patch,
    put,
)
from fastapi_control.controller import APIControllerRouter
from fastapi_control.di import factory, instantiate


@controller(prefix="/ops")
class OpsController(APIController):
    @put(path="/item")
    def put_item(self) -> dict[str, str]:
        return {"method": "put"}

    @patch(path="/item")
    def patch_item(self) -> dict[str, str]:
        return {"method": "patch"}

    @delete(path="/item")
    def delete_item(self) -> dict[str, str]:
        return {"method": "delete"}


@pytest.fixture()
def ops_client() -> TestClient:
    api = FastAPI()
    add_controller(api, OpsController)
    return TestClient(api)


def test_put_endpoint(ops_client: TestClient) -> None:
    response = ops_client.put("/ops/item")
    assert response.status_code == 200
    assert response.json() == {"method": "put"}


def test_patch_endpoint(ops_client: TestClient) -> None:
    response = ops_client.patch("/ops/item")
    assert response.status_code == 200
    assert response.json() == {"method": "patch"}


def test_delete_endpoint(ops_client: TestClient) -> None:
    response = ops_client.delete("/ops/item")
    assert response.status_code == 200
    assert response.json() == {"method": "delete"}


def test_api_route_decorator_registers_dual_paths() -> None:
    router = APIControllerRouter()

    @router.get("/direct")
    def direct() -> dict[str, str]:
        return {"via": "api_route"}

    api = FastAPI()
    api.include_router(router)
    client = TestClient(api)
    assert client.get("/direct").status_code == 200
    assert client.get("/direct/").status_code == 200
    assert client.get("/direct").json() == {"via": "api_route"}


def test_api_controller_get_router_requires_override() -> None:
    with pytest.raises(NotImplementedError):
        APIController.get_router()


def test_instantiate_calls_factory() -> None:
    class Service:
        pass

    result = instantiate(factory(Service))
    assert isinstance(result, Service)
    assert result is not Service()
