from typing import Any


class SingletonMeta(type):
    _instances = dict['SingletonMeta', 'SingletonMeta']()

    def __call__(cls, *args: tuple[Any, ...], **kwargs: Any):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
