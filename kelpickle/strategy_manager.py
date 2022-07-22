from __future__ import annotations
from typing import Type, Optional

from kelpickle.strategy.base_strategy import BaseStrategy


class StrategyConflictError(ValueError):
    pass


__type_to_strategy: dict[type, Type[BaseStrategy]] = {}
__name_to_strategy: dict[str, Type[BaseStrategy]] = {}


def register_strategy(cls: Type[BaseStrategy]):
    for type_ in cls.get_supported_types():
        if type_ in __type_to_strategy and __type_to_strategy[type_] is not cls:
            raise StrategyConflictError(f"Cannot configure type {type_} for strategy {cls}. It is already "
                                        f"taken by {__type_to_strategy[type_]}")
        __type_to_strategy[type_] = cls

    strategy_name = cls.get_strategy_name()
    if strategy_name in __name_to_strategy and __name_to_strategy[strategy_name] is not cls:
        raise StrategyConflictError(f"Cannot configure \"{strategy_name}\" for strategy {cls}. It is "
                                    f"already taken by {__name_to_strategy[strategy_name]}")

    __name_to_strategy[strategy_name] = cls

    return cls


def get_strategy_by_name(strategy_name: str) -> Optional[Type[BaseStrategy]]:
    return __name_to_strategy.get(strategy_name)


def get_strategy_by_type(type_: type) -> Optional[Type[BaseStrategy]]:
    return __type_to_strategy.get(type_)
