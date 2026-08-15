"""Smoke test against the example application."""

from fastapi.testclient import TestClient

from example.main import api, other_api


def test_example_greet_endpoints() -> None:
    client = TestClient(api)
    assert client.get("/home/greet").json() == "Hello, world!"
    assert client.get("/home/spanish_greet").json() == "Hola, mundo!"
    assert client.get("/home/nested_greet").json() == "Hola, mundo!"


def test_example_other_api_greet_endpoints() -> None:
    client = TestClient(other_api)
    assert client.get("/home/greet").json() == "Hello, world!"
    assert client.get("/home/spanish_greet").json() == "Hola, mundo!"
    assert client.get("/home/nested_greet").json() == "Hola, mundo!"
