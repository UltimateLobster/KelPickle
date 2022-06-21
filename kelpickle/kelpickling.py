from __future__ import annotations

import json

from typing import Type, Any, Callable
from kelpickle.common import NATIVE_TYPES, SimplifiedObject
from kelpickle.strategies.base_strategy import BaseStrategy
from kelpickle.strategies.state_strategy import StateStrategy
from kelpickle.strategies.reduce_strategy import ReduceStrategy
from kelpickle.strategies.null_strategy import NullStrategy
from kelpickle.strategies.list_strategy import ListStrategy
from kelpickle.strategies.dict_strategy import DictStrategy
from kelpickle.strategy_manager import get_strategy_by_name, get_strategy_by_type


DEFAULT_REDUCE = object.__reduce__
DEFAULT_REDUCE_EX = object.__reduce_ex__
STRATEGY_KEY = 'py/strategy'


class PicklingError(Exception):
    """
    Error that occurs during the pickling process
    """
    pass


class UnpicklingError(Exception):
    """
    Error that occurs during the unpickling process
    """
    pass


class UnsupportedStrategy(UnpicklingError):
    """
    Error that occurs if encountered an object that was pickled using an unsupported strategy
    """
    pass


class Pickler:
    def pickle(self, instance: Any) -> str:
        return json.dumps(self.simplify(instance))

    def simplify(self, instance: Any) -> SimplifiedObject:
        instance_type = instance.__class__
        strategy = get_strategy_by_type(instance_type)
        if strategy is None:
            return Pickler.default_simplify(instance, self)

        return self.simplify_with_strategy(instance, strategy)

    def simplify_with_strategy(self, instance: Any, strategy: Type[BaseStrategy]) -> SimplifiedObject:
        simplified_instance = strategy.simplify(instance, self)
        return SimplifiedObject(strategy.get_strategy_name(), simplified_instance)

    @staticmethod
    def default_simplify(instance: Any, pickler: Pickler) -> SimplifiedObject:
        instance_type = instance.__class__
        if instance_type.__reduce_ex__ == DEFAULT_REDUCE_EX and instance_type.__reduce__ == DEFAULT_REDUCE:
            # We have no custom implementation of __reduce__/__reduce_ex__. We may use the state shortcut instead.
            strategy = StateStrategy
        else:
            strategy = ReduceStrategy

        return pickler.simplify_with_strategy(instance, strategy)


def restore_by_dynamic_strategy(simplified_instance: SimplifiedObject, unpickler: Unpickler) -> Any:
    """
    Restore objects whose strategy is derived from their value (instead of their type).

    :param simplified_instance: The flattened object to restore
    :param unpickler: The unpickler to be used for any inner members that should be restored as well.
    :return: The original object as was passed to the "simplify" function
    """

    strategy_name = simplified_instance.strategy_name
    if strategy_name:
        strategy = get_strategy_by_name(strategy_name)
        if strategy is None:
            raise UnsupportedStrategy(f'Received an unsupported strategy name: {strategy_name}', strategy_name)
    else:
        strategy = DictStrategy

    return strategy.restore(simplified_instance.simplified_instance, unpickler)


class Unpickler:
    simplified_type_to_restorer: dict[type, Callable[[SimplifiedObject, Unpickler], Any]] = {
        dict: restore_by_dynamic_strategy,
        list: ListStrategy.restore,
        **{native_type: NullStrategy.restore for native_type in NATIVE_TYPES}
    }

    def unpickle(self, serialized_instance: str) -> Any:
        return self.restore(json.loads(serialized_instance))

    def restore(self, simplified_instance: SimplifiedObject) -> Any:
        restorer = Unpickler.simplified_type_to_restorer.get(simplified_instance.__class__)
        if not restorer:
            raise UnpicklingError(f'Cannot restore object of type {simplified_instance.__class__}.')
        return restorer(simplified_instance, self)
