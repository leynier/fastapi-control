from fastapi import FastAPI
from fastapi_control import (
    APIController,
    add_controller,
    add_controllers,
    controller,
    get,
    inject,
)


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


# With the @controller decorator and inheriting from APIController, we can
# declare class-based routing (also called controller) and it has the same
# parameters as FastAPI's APIRouter
@controller(prefix="/home")
class HomeController(APIController):
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

# If you want to have multiple FastAPI instances with different controllers,
# you can use the add_controller method to add the desired controllers to
# the desired FastAPI instance one by one.
other_api = FastAPI()
add_controller(other_api, HomeController)
