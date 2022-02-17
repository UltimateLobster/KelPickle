from __future__ import annotations

import json

from typing import Type, Callable, Any, TypeVar
from types import FunctionType, ModuleType
from kelpickle.common import NATIVE_TYPES, identity, STRATEGY_KEY, Json, Jsonable, JsonList
from kelpickle.strategies.base_strategy import BaseStrategy
from kelpickle.strategies.dict_strategy import DictStrategy
from kelpickle.strategies.import_strategy import ImportStrategy
from kelpickle.strategies.reduce_strategy import ReduceStrategy
from kelpickle.strategies.set_strategy import SetStrategy
from kelpickle.strategies.tuple_strategy import TupleStrategy
from kelpickle.strategies.list_strategy import ListStrategy
from kelpickle.strategies.state_strategy import StateStrategy


DEFAULT_REDUCE = object.__reduce__
DEFAULT_REDUCE_EX = object.__reduce_ex__


class PicklingError(Exception):
    """
    Error that occurs during the pickling process
    """
    pass


T = TypeVar('T')


def identity_flatten(instance: T, pickler: Pickler) -> T:
    return instance


def default_flatten(instance: Any, pickler: Pickler) -> Jsonable:
    instance_class = type(instance)
    if instance_class.__reduce_ex__ == DEFAULT_REDUCE_EX and instance_class.__reduce__ == DEFAULT_REDUCE:
        # We have no custom implementation of __reduce__/__reduce_ex__. We may use the state syntactic sugar instead.
        return StateStrategy.flatten(instance, pickler)

    return ReduceStrategy.flatten(instance, pickler)


class Pickler:
    type_to_flattener: dict[Type[Any], Callable[[Any, Pickler], Jsonable]] = {
        list: ListStrategy.flatten,
        dict: DictStrategy.flatten,
        type: ImportStrategy.flatten,
        FunctionType: ImportStrategy.flatten,
        ModuleType: ImportStrategy.flatten,
        set: SetStrategy.flatten,
        tuple: TupleStrategy.flatten,
        **{native_type: identity_flatten for native_type in NATIVE_TYPES}
    }

    def pickle(self, instance: Any) -> str:
        return json.dumps(self.flatten(instance))

    def flatten(self, instance: Any) -> Jsonable:
        instance_type = instance.__class__
        flattener = self.type_to_flattener.get(instance_type, default_flatten)

        return flattener(instance, self)
