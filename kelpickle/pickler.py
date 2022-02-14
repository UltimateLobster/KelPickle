from __future__ import annotations

import json

from typing import Type, Callable, Any
from types import FunctionType, ModuleType
from kelpickle.common import NATIVE_TYPES, identity, STRATEGY_KEY, Json, Jsonable, JsonList
from kelpickle.strategies.base_strategy import BaseStrategy
from kelpickle.strategies.dict_strategy import DictStrategy
from kelpickle.strategies.import_strategy import ImportStrategy
from kelpickle.strategies.reduce_strategy import ReduceStrategy
from kelpickle.strategies.set_strategy import SetStrategy
from kelpickle.strategies.tuple_strategy import TupleStrategy


class PicklingError(Exception):
    """
    Error that occurs during the pickling process
    """
    pass


class Pickler:
    type_to_strategy: dict[type, Type[BaseStrategy]] = {
        type: ImportStrategy,
        FunctionType: ImportStrategy,
        ModuleType: ImportStrategy,
        set: SetStrategy,
        tuple: TupleStrategy,
    }

    def __init__(self) -> None:
        self.type_to_flattener: dict[Type[Any], Callable[[Any], Jsonable]] = {
            list: self.flatten_by_list,
            dict: self.flatten_by_dict,
            **{native_type: identity for native_type in NATIVE_TYPES}
        }

    def pickle(self, instance: Any) -> str:
        return json.dumps(self.flatten(instance))

    def flatten(self, instance: Any) -> Jsonable:
        instance_type = instance.__class__
        flattener = self.type_to_flattener.get(instance_type, self.flatten_by_strategy)

        return flattener(instance)

    def flatten_by_strategy(self, instance: Any) -> Json:
        instance_type = instance.__class__
        strategy = Pickler.type_to_strategy.get(instance_type, ReduceStrategy)

        jsonified_instance = strategy.flatten(instance, self)
        jsonified_instance[STRATEGY_KEY] = strategy.get_strategy_name()

        return jsonified_instance

    def flatten_by_list(self, instance: list) -> JsonList:
        return [self.flatten(member) for member in instance]

    def flatten_by_dict(self, instance: dict) -> Json:
        flattened_instance = DictStrategy.flatten(instance, self)

        return flattened_instance
