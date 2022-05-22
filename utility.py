from typing import Any

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PALE = (255, 245, 219)
BROWN = (82, 64, 53)
YELLOW = (255, 255, 0)
BG = (52, 95, 110)


class GameEvent:
    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            self.__setattr__(k, v)
        self.__handlers = []

    def __iadd__(self, handler: Any) -> 'GameEvent':
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler: Any) -> 'GameEvent':
        self.__handlers.remove(handler)
        return self

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        for handler in self.__handlers.copy():
            handler(*args, **kwargs)
