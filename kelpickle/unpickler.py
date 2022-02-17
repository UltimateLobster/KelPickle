from __future__ import annotations

import json

from typing import Callable, Type, Any, Iterable, TypeVar

from kelpickle.common import NATIVE_TYPES, identity, STRATEGY_KEY, Json, Jsonable
from kelpickle.strategies.base_strategy import BaseStrategy, JsonStrategy
from kelpickle.strategies.dict_strategy import DictStrategy
from kelpickle.strategies.import_strategy import ImportStrategy
from kelpickle.strategies.reduce_strategy import ReduceStrategy
from kelpickle.strategies.set_strategy import SetStrategy
from kelpickle.strategies.state_strategy import StateStrategy
from kelpickle.strategies.tuple_strategy import TupleStrategy
from kelpickle.strategies.list_strategy import ListStrategy


class UnsupportedStrategy(ValueError):
    pass


T = TypeVar('T')


def identity_restore(instance: T, unpickler: Unpickler) -> T:
    return instance


def restore_by_strategy(flattened_instance: Json, unpickler: Unpickler) -> Any:
    """
    Restore non-jsonic objects that has to be represented by a dict

    :param flattened_instance: The flattened object to restore
    :param unpickler: The unpickler to be used for any inner members that should be restored as well.
    :return: The original object as was passed to the "flatten" function
    """

    strategy_name = flattened_instance.pop(STRATEGY_KEY, 'dict')
    try:
        strategy = Unpickler.name_to_strategy[strategy_name]
    except KeyError as e:
        raise UnsupportedStrategy(f'Received an unsupported strategy name: {strategy_name}', strategy_name) from e

    return strategy.restore(flattened_instance, unpickler)


class Unpickler:
    SUPPORTED_STRATEGIES: Iterable[Type[JsonStrategy]] = (
        ImportStrategy,
        SetStrategy,
        TupleStrategy,
        StateStrategy,
        ReduceStrategy,
        DictStrategy
    )
    name_to_strategy: dict[str, Type[BaseStrategy]] = {
        strategy.get_strategy_name(): strategy
        for strategy in SUPPORTED_STRATEGIES
    }

    flattened_type_to_restore_function: dict[type, Callable[[Jsonable, Unpickler], Any]] = {
        list: ListStrategy.restore,
        dict: restore_by_strategy,
        **{native_type: identity_restore for native_type in NATIVE_TYPES}
    }

    def unpickle(self, serialized_instance: str) -> Any:
        return self.restore(json.loads(serialized_instance))

    def restore(self, flattened_instance: Jsonable) -> Any:
        restorer = self.flattened_type_to_restore_function[flattened_instance.__class__]
        return restorer(flattened_instance, self)
