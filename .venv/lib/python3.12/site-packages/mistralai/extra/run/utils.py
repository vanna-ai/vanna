import importlib.util
import sys
from typing import Callable, TypeVar, Any, cast
from functools import wraps

from mistralai.extra.exceptions import MistralClientException

F = TypeVar("F", bound=Callable[..., Any])


REQUIRED_PYTHON_VERSION = (3, 10)
REQUIRED_PYTHON_VERSION_STR = "3.10"
REQUIRED_PACKAGES = ["mcp"]


def is_module_installed(module_name: str) -> bool:
    spec = importlib.util.find_spec(module_name)
    return spec is not None


def run_requirements(func: F) -> F:
    @wraps(func)
    def wrapper(*args, **kwargs):
        if sys.version_info < REQUIRED_PYTHON_VERSION:
            raise MistralClientException(
                f"{func.__name__} requires a Python version higher than {REQUIRED_PYTHON_VERSION_STR}."
                f"You are using Python {sys.version_info.major}.{sys.version_info.minor}."
            )
        for package in REQUIRED_PACKAGES:
            if not is_module_installed(package):
                raise MistralClientException(
                    f"{func.__name__} requires the sdk to be installed with 'agents' extra dependencies."
                )
        return func(*args, **kwargs)

    return cast(F, wrapper)
