# Welcome to FastAPI Control 👋

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Last commit](https://img.shields.io/github/last-commit/leynier/fastapi-control.svg?style=flat)](https://github.com/leynier/fastapi-control/commits)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/leynier/fastapi-control)](https://github.com/leynier/fastapi-control/commits)
[![Github Stars](https://img.shields.io/github/stars/leynier/fastapi-control?style=flat&logo=github)](https://github.com/leynier/fastapi-control/stargazers)
[![Github Forks](https://img.shields.io/github/forks/leynier/fastapi-control?style=flat&logo=github)](https://github.com/leynier/fastapi-control/network/members)
[![Github Watchers](https://img.shields.io/github/watchers/leynier/fastapi-control?style=flat&logo=github)](https://github.com/leynier/fastapi-control)
[![GitHub contributors](https://img.shields.io/github/contributors/leynier/fastapi-control)](https://github.com/leynier/fastapi-control/graphs/contributors)

> FastAPI utility to implement class-based routing with controllers and dependency injection.

## Install

```sh
pip install git+https://github.com/leynier/fastapi-control@main
```

## Usage

```python
from fastapi import FastAPI

from fastapi_control import add_controllers, controller, get, inject


# Optionally declares an abstraction
class GreeterAbstraction:
    def greet(self):
        raise NotImplementedError()


# Implement the abstraction and make it available to the injection system
# using the @inject decorator
@inject(alias=GreeterAbstraction)
class GretterImplementation:
    def greet(self):
        return "Hello, world!"


# It is also possible to implement without abstraction and make it available
# to the injection system directly
@inject()
class SpanishGretterImplementation:
    def greet(self):
        return "Hola, mundo!"


@inject()
class NestedGretterImplementation:
    # When the @inject decorator is used, the arguments of the __init__
    # method are automatically injected (if the @inject decorator was used
    # in the argument type declarations)
    def __init__(self, spanish_gretter: SpanishGretterImplementation) -> None:
        self.gretter = spanish_gretter

    def greet(self):
        return self.gretter.greet()


# With the @controller decorator, we can declare class-based routing (also
# called controller) and it has the same parameters as FastAPI's APIRouter
@controller(prefix="/home")
class HomeController:
    # When the @controller decorator is used, the arguments of the __init__
    # method are automatically injected (if the @inject decorator was used
    # in the argument type declarations)
    def __init__(
        self,
        gretter: GreeterAbstraction,
        spanish_gretter: SpanishGretterImplementation,
        nested_gretter: NestedGretterImplementation,
    ) -> None:
        self.gretter = gretter
        self.spanish_gretter = spanish_gretter
        self.nested_gretter = nested_gretter

    # The @get decorator declares the method as a GET endpoint (there are
    # also @post, @put, @delete, @patch decorators) and the behavior is the
    # same as the corresponding FastAPI decorators.
    @get(path="/greet")
    def get_greet(self):
        return self.gretter.greet()

    @get(path="/spanish_greet")
    def get_spanish_greet(self):
        return self.spanish_gretter.greet()

    @get(path="/nested_greet")
    def get_nested_greet(self):
        return self.nested_gretter.greet()


api = FastAPI()
# Finally, it is necessary to add the controllers to the FastAPI instance
add_controllers(api)
```

## Inspirations

This project is based on and inspired by the [NEXTX](https://github.com/adriangs1996/nextx.repository) and [FastApi-RESTful](https://github.com/yuval9313/FastApi-RESTful) projects.

The difference with [FastApi-RESTful](https://github.com/yuval9313/FastApi-RESTful) is that **FastAPI Control** implements an automatic dependency injection system independent of [FastAPI](https://fastapi.tiangolo.com).

The difference with [NEXTX](https://github.com/adriangs1996/nextx.repository) is that **FastAPI Control** only aims to solve the problem of class-based routes and automatic dependency injection, and uses the [kink](https://github.com/kodemore/kink) library for dependency injection which is still under maintenance while [NEXTX](https://github.com/adriangs1996/nextx.repository) uses [python-inject](https://github.com/ivankorobkov/python-inject) which has not been maintained since 2020.

Many thanks to the creators and maintainers of those projects for providing inspiration and guidance for this one.

## Authors

👨🏻‍💻 **Leynier Gutiérrez González**

* Website: [leynier.dev](https://leynier.dev)
* LinkedIn: [@leynier](https://linkedin.com/in/leynier)
* Github: [@leynier](https://github.com/leynier)
* Twitter: [@leynier41](https://twitter.com/leynier41)

## 🤝 Contributing

Contributions, issues and feature requests are welcome!<br />Feel free to check [issues page](https://github.com/leynier/fastapi-control/issues). You can also take a look at the [contributing guide](CONTRIBUTING.md).

## Show your support

Give a ⭐️ if this project helped you!
