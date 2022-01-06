from __future__ import annotations

import json

from typing import Callable, Type, Any

from kelpickle.common import NATIVE_TYPES, identity, STRATEGY_KEY
from kelpickle.strategies.base_strategy import BaseStrategy
from kelpickle.strategies.dict_strategy import DictStrategy
from kelpickle.strategies.import_strategy import ImportStrategy
from kelpickle.strategies.reduce_strategy import ReduceStrategy
from kelpickle.strategies.set_strategy import SetStrategy
from kelpickle.strategies.state_strategy import StateStrategy
from kelpickle.strategies.tuple_strategy import TupleStrategy


class UnsupportedStrategy(ValueError):
    pass


class Unpickler:
    name_to_strategy: dict[str, Type[BaseStrategy]] = {
        strategy.get_strategy_name(): strategy
        for strategy in (
            ImportStrategy,
            SetStrategy,
            TupleStrategy,
            StateStrategy,
            ReduceStrategy,
            DictStrategy
        )
    }

    def __init__(self):
        self.flattened_type_to_restore_function: dict[type, Callable[[Any], Any]] = {
            list: self.restore_by_list,
            dict: self.restore_by_strategy,
            **{native_type: identity for native_type in NATIVE_TYPES}
        }

    def unpickle(self, serialized_instance):
        return self.restore(json.loads(serialized_instance))

    def restore(self, flattened_instance):
        restorer = self.flattened_type_to_restore_function[flattened_instance.__class__]
        return restorer(flattened_instance)

    def restore_by_strategy(self, flattened_instance: dict):
        """
        Restore non-jsonic objects that has to be represented by a dict

        :param flattened_instance: The flattened object to restore
        :return: The original object as was passed to the "flatten" function
        """

        strategy_name = flattened_instance.get(STRATEGY_KEY, 'dict')
        try:
            strategy = Unpickler.name_to_strategy[strategy_name]
        except KeyError as e:
            raise UnsupportedStrategy(f'Received an unsupported strategy name: {strategy_name}', strategy_name) from e

        return strategy.restore(flattened_instance, self)

    def restore_by_list(self, flattened_instance: list):
        return [self.restore(member) for member in flattened_instance]
