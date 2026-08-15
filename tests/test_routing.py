"""Tests for route registration behavior of APIControllerRouter."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastapi_control import APIController, add_controller, controller, get, post


@controller(prefix="/items")
class ItemsController(APIController):
    @get(path="/{item_id}")
    def get_item(self, item_id: int) -> dict[str, object]:
        return {"item_id": item_id, "via": "item"}

    @post(path="/")
    def create_item(self, name: str) -> dict[str, object]:
        return {"created": name}


@pytest.fixture()
def items_api() -> FastAPI:
    api = FastAPI()
    add_controller(api, ItemsController)
    return api


@pytest.fixture()
def items_client(items_api: FastAPI) -> TestClient:
    return TestClient(items_api)


def test_get_endpoint(items_client: TestClient) -> None:
    response = items_client.get("/items/1")
    assert response.status_code == 200
    assert response.json() == {"item_id": 1, "via": "item"}


def test_post_endpoint(items_client: TestClient) -> None:
    response = items_client.post("/items", params={"name": "foo"})
    assert response.status_code == 200
    assert response.json() == {"created": "foo"}


def test_trailing_slash_responds_on_both_variants(items_client: TestClient) -> None:
    with_trailing = items_client.get("/items/7/")
    without_trailing = items_client.get("/items/7")
    assert with_trailing.status_code == 200
    assert without_trailing.status_code == 200
    assert with_trailing.json() == without_trailing.json()


def test_trailing_slash_on_collection_root(items_client: TestClient) -> None:
    assert items_client.post("/items", params={"name": "a"}).status_code == 200
    assert items_client.post("/items/", params={"name": "b"}).status_code == 200


def test_root_path_is_in_openapi_schema_and_responds() -> None:
    @controller()
    class RootController(APIController):
        @get(path="/")
        def root(self) -> dict[str, str]:
            return {"hello": "root"}

    api = FastAPI()
    add_controller(api, RootController)
    client = TestClient(api)

    paths = api.openapi()["paths"]
    # FastAPI rejects routes with an empty final path, so the root endpoint
    # is exposed under "/" and honors include_in_schema
    assert "/" in paths
    assert client.get("/").status_code == 200
    assert client.get("/").json() == {"hello": "root"}


def test_prefixed_root_path_is_in_openapi_schema_and_responds() -> None:
    @controller(prefix="/api")
    class PrefixedRootController(APIController):
        @get(path="/")
        def root(self) -> dict[str, str]:
            return {"hello": "prefixed"}

    api = FastAPI()
    add_controller(api, PrefixedRootController)
    client = TestClient(api)

    paths = api.openapi()["paths"]
    assert "/api" in paths
    assert "/api/" not in paths
    assert client.get("/api").json() == {"hello": "prefixed"}
    assert client.get("/api/").json() == {"hello": "prefixed"}


@controller(prefix="/users")
class UsersController(APIController):
    @get(path="/me")
    def me(self) -> dict[str, str]:
        return {"user": "me"}

    @get(path="/{user_id}")
    def get_user(self, user_id: str) -> dict[str, str]:
        return {"user": user_id}


def test_route_order_follows_definition_order_me_first() -> None:
    """/me is declared before /{user_id}, so it must win for GET /users/me."""
    api = FastAPI()
    add_controller(api, UsersController)
    client = TestClient(api)

    assert client.get("/users/me").json() == {"user": "me"}
    assert client.get("/users/42").json() == {"user": "42"}


def test_router_registers_routes_in_definition_order() -> None:
    @controller(prefix="/ordered")
    class OrderedController(APIController):
        @get(path="/first")
        def first(self) -> dict[str, str]:
            return {"n": "1"}

        @get(path="/second")
        def second(self) -> dict[str, str]:
            return {"n": "2"}

        @get(path="/third")
        def third(self) -> dict[str, str]:
            return {"n": "3"}

    schema_paths = list(OrderedController.get_router().routes)
    visible_paths = [route.path for route in schema_paths if route.include_in_schema]
    assert visible_paths == ["/ordered/first", "/ordered/second", "/ordered/third"]


def test_route_order_is_deterministic_across_registrations() -> None:
    """Registering the same controller on two apps must yield the same path order."""
    paths = []
    for _ in range(2):
        api = FastAPI()
        add_controller(api, UsersController)
        paths.append(
            [
                route.path
                for route in api.routes
                if getattr(route, "include_in_schema", False)
            ]
        )
    assert paths[0] == paths[1]
