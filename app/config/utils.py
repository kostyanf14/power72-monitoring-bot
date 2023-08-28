import os
from typing import Callable, Optional, TypeVar

T = TypeVar('T')


def getenv(key: str, default: Optional[str] = None) -> str:
    value = os.getenv(key)
    if value is not None:
        return value
    if default is not None:
        return default
    raise ValueError(f"Environment variable {key} is not set")


def getenv_typed(key: str, cast: Callable[[str], T], default: Optional[T] = None) -> T:
    value = os.getenv(key)
    if value is not None:
        return cast(value)
    if default is not None:
        return default
    raise ValueError(f"Environment variable {key} is not set")
