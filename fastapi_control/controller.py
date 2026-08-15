"""Class-based routing for FastAPI with controllers and dependency injection."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from enum import Enum
from inspect import Parameter, isfunction, signature
from typing import Any, ParamSpec, TypeVar

from fastapi import APIRouter, Depends, FastAPI, Response, params
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.types import DecoratedCallable
from fastapi.utils import generate_unique_id
from starlette.routing import BaseRoute
from starlette.types import ASGIApp

from .di import factory, inject

ROUTER_KEY = "__api_router__"
ENDPOINT_KEY = "__endpoint_api_key__"


def _split_path(path: str) -> tuple[str, str]:
    """Return the non-trailing-slash and trailing-slash variants of a path."""
    path_no_slash = path[:-1] if path.endswith("/") else path
    return path_no_slash, path_no_slash + "/"


class APIControllerRouter(APIRouter):
    """
    Registers endpoints for both a non-trailing-slash and a trailing slash.
    In regards to the exported API schema only the non-trailing slash will be included.
    Examples:
        @router.get("") - included in the OpenAPI schema as the naked url,
        responds to both the naked url (no slash) and /
        @router.get("/some/path") - included in the OpenAPI schema as /some/path,
        responds to both /some/path and /some/path/
        @router.get("/some/path/") - included in the OpenAPI schema as /some/path,
        responds to both /some/path and /some/path/
    Co-opted from https://github.com/tiangolo/fastapi/issues/2060#issuecomment-974527690
    """

    def api_route(
        self,
        path: str,
        *,
        include_in_schema: bool = True,
        **kwargs: Any,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            self.add_dual_api_route(
                path, func, include_in_schema=include_in_schema, **kwargs
            )
            return func

        return decorator

    def add_dual_api_route(
        self,
        path: str,
        endpoint: DecoratedCallable,
        *,
        include_in_schema: bool = True,
        **kwargs: Any,
    ) -> None:
        """Add an API route that responds on both the non-trailing-slash and
        the trailing-slash variants of ``path``.

        Only the non-trailing-slash variant is included in the OpenAPI schema.
        FastAPI rejects routes whose final path is empty, so when ``path``
        resolves to the root (``/``) and this router has no prefix, only the
        ``/`` route is registered (honoring ``include_in_schema``).
        """
        path_no_slash, path_with_slash = _split_path(path)
        if path_no_slash == "" and not self.prefix:
            super().add_api_route(
                path_with_slash,
                endpoint,
                include_in_schema=include_in_schema,
                **kwargs,
            )
            return
        super().add_api_route(
            path_with_slash, endpoint, include_in_schema=False, **kwargs
        )
        super().add_api_route(
            path_no_slash, endpoint, include_in_schema=include_in_schema, **kwargs
        )


class APIController:
    @staticmethod
    def get_router() -> APIControllerRouter:
        raise NotImplementedError


__controllers__: list[type[APIController]] = []


def reset_controllers() -> None:
    """Clear the global controller registry.

    Every class decorated with :func:`controller` is appended to the global
    ``__controllers__`` registry so that :func:`add_controllers` can mount all
    of them at once. This function empties that registry, which is mainly
    useful to isolate tests that define their own controllers.
    """
    __controllers__.clear()


T = TypeVar("T", bound=APIController)
ARG = ParamSpec("ARG")
RET = TypeVar("RET")


@dataclass
class RouteArgs:
    """The arguments APIRouter.add_api_route takes.
    Just a convenience for type safety and so we can pass all the args
    needed by the underlying FastAPI route args via
    `**dataclasses.asdict(some_args)`.
    """

    path: str
    response_model: type[Any] | None = None
    status_code: int | None = None
    tags: list[str] | None = None
    dependencies: Sequence[params.Depends] | None = None
    summary: str | None = None
    description: str | None = None
    response_description: str = "Successful Response"
    responses: dict[int | str, dict[str, Any]] | None = None
    deprecated: bool | None = None
    methods: set[str] | list[str] | None = None
    operation_id: str | None = None
    response_model_include: set[int | str] | dict[int | str, Any] | None = None
    response_model_exclude: set[int | str] | dict[int | str, Any] | None = None
    response_model_by_alias: bool = True
    response_model_exclude_unset: bool = False
    response_model_exclude_defaults: bool = False
    response_model_exclude_none: bool = False
    include_in_schema: bool = True
    response_class: type[Response] | DefaultPlaceholder = field(
        default_factory=lambda: Default(JSONResponse)
    )
    name: str | None = None
    route_class_override: type[APIRoute] | None = None
    callbacks: list[BaseRoute] | None = None
    openapi_extra: dict[str, Any] | None = None


def get(
    path: str,
    **kwargs: Any,
) -> Callable[[Callable[ARG, RET]], Callable[ARG, RET]]:
    """Mark a controller method as a GET endpoint."""

    def decorator(fn: Callable[ARG, RET]) -> Callable[ARG, RET]:
        endpoint = RouteArgs(path=path, methods=["GET"], **kwargs)
        setattr(fn, ENDPOINT_KEY, endpoint)
        return fn

    return decorator


def post(
    path: str,
    **kwargs: Any,
) -> Callable[[Callable[ARG, RET]], Callable[ARG, RET]]:
    """Mark a controller method as a POST endpoint."""

    def decorator(fn: Callable[ARG, RET]) -> Callable[ARG, RET]:
        endpoint = RouteArgs(path=path, methods=["POST"], **kwargs)
        setattr(fn, ENDPOINT_KEY, endpoint)
        return fn

    return decorator


def put(
    path: str,
    **kwargs: Any,
) -> Callable[[Callable[ARG, RET]], Callable[ARG, RET]]:
    """Mark a controller method as a PUT endpoint."""

    def decorator(fn: Callable[ARG, RET]) -> Callable[ARG, RET]:
        endpoint = RouteArgs(path=path, methods=["PUT"], **kwargs)
        setattr(fn, ENDPOINT_KEY, endpoint)
        return fn

    return decorator


def patch(
    path: str,
    **kwargs: Any,
) -> Callable[[Callable[ARG, RET]], Callable[ARG, RET]]:
    """Mark a controller method as a PATCH endpoint."""

    def decorator(fn: Callable[ARG, RET]) -> Callable[ARG, RET]:
        endpoint = RouteArgs(path=path, methods=["PATCH"], **kwargs)
        setattr(fn, ENDPOINT_KEY, endpoint)
        return fn

    return decorator


def delete(
    path: str,
    **kwargs: Any,
) -> Callable[[Callable[ARG, RET]], Callable[ARG, RET]]:
    """Mark a controller method as a DELETE endpoint."""

    def decorator(fn: Callable[ARG, RET]) -> Callable[ARG, RET]:
        endpoint = RouteArgs(path=path, methods=["DELETE"], **kwargs)
        setattr(fn, ENDPOINT_KEY, endpoint)
        return fn

    return decorator


def controller(
    *,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[params.Depends] | None = None,
    default_response_class: type[Response] = Default(JSONResponse),
    responses: dict[int | str, dict[str, Any]] | None = None,
    callbacks: list[BaseRoute] | None = None,
    routes: list[BaseRoute] | None = None,
    redirect_slashes: bool = True,
    default: ASGIApp | None = None,
    dependency_overrides_provider: Any = None,
    route_class: type[APIRoute] = APIRoute,
    on_startup: Sequence[Callable[[], Any]] | None = None,
    on_shutdown: Sequence[Callable[[], Any]] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    generate_unique_id_function: Callable[[APIRoute], str] = Default(
        generate_unique_id
    ),
) -> Callable[[type[T]], type[T]]:
    """
    Returns a decorator that makes a Class-Based-View (or a controller)
    out of a regular python class.
    Decorated class should not define constructor arguments, other than
    dependencies. All arguments would be treated as injection parameters, and
    type-hints would be used as interface-resolvers for this dependencies.
    This decorator effectively decorates the class constructor with
    `inject` so any non-resolved dependency would
    issue an exception at runtime.
    When defining endpoints, dependency injection at endpoint-level should
    behave as expected in FastAPI
    Example
    =======
    >>> @controller(prefix='/controller-test', tags=['My Controller'])
    >>> class UsersController:
    >>>     def __init__(self, user_service: IUserService):
    >>>         self.user_service = user_service
    >>>
    >>>     @get('/{user_id}')
    >>>     async def get_users(self, user_id: str = Path(...)):
    >>>         return await self.user_service.get_by_id(user_id)
    """
    router = APIControllerRouter(
        prefix=prefix,
        tags=tags,
        dependencies=dependencies,
        default_response_class=default_response_class,
        responses=responses,
        callbacks=callbacks,
        routes=routes,
        redirect_slashes=redirect_slashes,
        default=default,
        dependency_overrides_provider=dependency_overrides_provider,
        route_class=route_class,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        generate_unique_id_function=generate_unique_id_function,
    )

    def decorator(cls: type[T]) -> type[T]:
        setattr(cls, "get_router", staticmethod(lambda: router))  # noqa: B010
        if not router.tags:
            tag = cls.__name__
            if tag.endswith("Controller"):
                tag = tag[:-10]
            router.tags.append(tag)
        # inject the underlying router in the class
        return _controller(router, cls)

    return decorator


def _resolve_endpoint_functions(cls: type[Any]) -> list[Callable[..., Any]]:
    """
    Collect the endpoint-decorated functions of `cls` in definition order.

    The MRO is walked from base classes to the most derived one, and each
    `__dict__` is visited in definition order, so endpoints are registered
    deterministically in the order they were declared. Endpoints overridden
    in a derived class replace the base-class ones while keeping the
    registration position of the first definition.
    """
    functions: dict[str, Callable[..., Any]] = {}
    for klass in reversed(cls.__mro__):
        for name, member in vars(klass).items():
            if isfunction(member):
                functions[name] = member
            elif isinstance(member, (staticmethod, classmethod)):
                functions[name] = member.__func__
    return [
        function
        for function in functions.values()
        if getattr(function, ENDPOINT_KEY, None) is not None
    ]


def _controller(router: APIControllerRouter, cls: type[T]) -> type[T]:
    """
    Replaces any methods of the provided class `cls` that are endpoints
    with updated function calls that will properly inject an instance of
    `cls`
    """
    # Make this class constructor based injectable
    wrapper = inject()
    cls = wrapper(cls)

    # get all endpoint functions in definition order
    endpoints = _resolve_endpoint_functions(cls)

    for endpoint in endpoints:
        _fix_endpoint_signature(cls, endpoint)
        # Add the corrected function to the router; it responds on both the
        # non-trailing-slash path (visible in the OpenAPI schema) and the
        # trailing-slash twin (hidden)
        args: RouteArgs = getattr(endpoint, ENDPOINT_KEY)
        route_kwargs = asdict(args)
        path = route_kwargs.pop("path")
        include_in_schema = route_kwargs.pop("include_in_schema")
        router.add_dual_api_route(
            path, endpoint, include_in_schema=include_in_schema, **route_kwargs
        )

    # register the router
    __controllers__.append(cls)
    return cls


def _fix_endpoint_signature(cls: type[Any], endpoint: Callable[..., Any]) -> None:
    old_signature = signature(endpoint)
    old_parameters: list[Parameter] = list(old_signature.parameters.values())

    # Endpoints that do not declare `self` as their first parameter (for
    # example `staticmethod` endpoints or module-level like functions) are
    # registered as-is, without controller instance injection.
    if not old_parameters or old_parameters[0].name != "self":
        return

    old_first_parameter = old_parameters[0]

    # Here we replace the function signature from:
    # >>> Class Test:
    # >>>   @post('/')
    # >>>   async def do_something(self, item: Item):
    # >>>       ...

    # To:

    # >>> Class Test:
    # >>>   @post('/')
    # >>>   async def do_something(self = Depends(factory(Test)), item: Item):
    # >>>       ...

    # With this new signature, FastAPI will instantiate the self argument
    # with each HTTP method call, and because of the `factory(cls)` returns
    # a parameterless function, FastAPI will know that this does not require
    # any dependency and will not document it.
    # For this to work, `cls` must effectively be wrapped on inject,
    # so it tries to inject all the constructor arguments at runtime
    new_self_parameter = old_first_parameter.replace(default=Depends(factory(cls)))
    new_parameters = [new_self_parameter] + [
        parameter.replace(kind=Parameter.KEYWORD_ONLY)
        for parameter in old_parameters[1:]
    ]

    new_signature = old_signature.replace(parameters=new_parameters)
    setattr(endpoint, "__signature__", new_signature)  # noqa: B010


def add_controller(
    api: FastAPI,
    controller: type[T],
    *,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[params.Depends] | None = None,
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    default_response_class: type[Response] = Default(JSONResponse),
    callbacks: list[BaseRoute] | None = None,
    generate_unique_id_function: Callable[[APIRoute], str] = Default(
        generate_unique_id
    ),
) -> None:
    """Include the routes of a single controller into the given FastAPI app.

    Useful when multiple FastAPI instances need different subsets of the
    registered controllers.
    """
    api.include_router(
        controller.get_router(),
        prefix=prefix,
        tags=tags,
        dependencies=dependencies,
        responses=responses,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        default_response_class=default_response_class,
        callbacks=callbacks,
        generate_unique_id_function=generate_unique_id_function,
    )


def add_controllers(
    api: FastAPI,
    *,
    prefix: str = "",
    tags: list[str | Enum] | None = None,
    dependencies: Sequence[params.Depends] | None = None,
    responses: dict[int | str, dict[str, Any]] | None = None,
    deprecated: bool | None = None,
    include_in_schema: bool = True,
    default_response_class: type[Response] = Default(JSONResponse),
    callbacks: list[BaseRoute] | None = None,
    generate_unique_id_function: Callable[[APIRoute], str] = Default(
        generate_unique_id
    ),
) -> None:
    """Include the routes of every registered controller into the given FastAPI app."""
    for controller in __controllers__:
        api.include_router(
            controller.get_router(),
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            responses=responses,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            default_response_class=default_response_class,
            callbacks=callbacks,
            generate_unique_id_function=generate_unique_id_function,
        )
