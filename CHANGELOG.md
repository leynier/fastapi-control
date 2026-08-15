# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-08-14

### Fixed

- Root endpoints (`@get("/")`, `@post("/")`, ...) are now exposed in the OpenAPI
  schema and honor the `include_in_schema` parameter, just like any other path.
- Route registration order is now deterministic and follows source definition
  order (base classes first, then the derived class), so declarations like
  `/me` before `/{id}` resolve as intended. Previously the order came from an
  unordered `set`, making first-match routes non-deterministic.
- Controllers now actually register both the non-trailing-slash and the
  trailing-slash variants of every endpoint, as documented (previously the
  trailing-slash twin was silently skipped and only a redirect made it work).
- Removed the `_Container` workaround: kink 0.9.0 resolves `alias` combined
  with `use_factory` natively, so `fastapi_control.di` now uses the stock
  kink `Container` directly.

### Added

- `reset_controllers()` to clear the global controller registry, mainly useful
  for test isolation.
- Support for `staticmethod` endpoints and endpoints that do not declare
  `self`: they are registered as-is, without controller instance injection.
- `py.typed` marker so type checkers see the inline types of the package.
- Test suite (routing, dependency injection, controller registry, example
  smoke tests).
- CI workflow (lint, type check and tests on Python 3.10, 3.12 and 3.14) and
  release workflow (trusted publishing to PyPI plus GitHub releases).
- `__all__` export list and docstrings for the public API.

### Changed

- Migrated to modern typing (`from __future__ import annotations`,
  built-in generics, `X | None` unions).
- Replaced the `black`/`flake8`/`isort` dev toolchain with `ruff` and added
  `mypy` (strict) to the dev dependencies.
- Bumped minimum supported versions: Python >= 3.10 and FastAPI >= 0.141.

## [0.4.0] and earlier

See the [commit history](https://github.com/leynier/fastapi-control/commits/main).
