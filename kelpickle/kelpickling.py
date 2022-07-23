from __future__ import annotations

import json
from pickle import DEFAULT_PROTOCOL

from typing import Type, Any, Callable, Optional

from kelpickle import DefaultStrategy
from kelpickle.common import NATIVE_TYPES, KELP_STRATEGY_KEY
from kelpickle.strategy.base_strategy import BaseStrategy, ReductionResult, JsonicReductionResult, \
    BaseNonNativeJsonStrategy
from kelpickle.strategy.null_strategy import NullStrategy
from kelpickle.strategy.list_strategy import ListStrategy
from kelpickle.strategy.dict_strategy import DictStrategy
from kelpickle.strategy_manager import get_strategy_by_name, get_strategy_by_type


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
    PICKLE_PROTOCOL = DEFAULT_PROTOCOL

    def pickle(self, instance: Any) -> str:
        """
        serialize the given python object.

        :param instance: The instance to serialize
        :return: The serialized instance
        """
        return json.dumps(self.reduce(instance))

    def reduce(self, instance: Any) -> ReductionResult:
        """
        Reduce the given instance to a simplified representation of the steps to rebuild it.
        :param instance: The instance to use_python_reduce
        :return: The reduced instance
        """
        instance_type = instance.__class__
        strategy = get_strategy_by_type(instance_type)
        if strategy is None:
            return self.default_reduce(instance)

        return self.reduce_by_strategy(instance, strategy)

    def default_reduce(self, instance: Any) -> ReductionResult:
        """
        Reduce an instance using the default strategy. This function is encouraged to be used by strategies that wish to
        "extend" the default strategy.

        :param instance: The instance to use_python_reduce
        :return: The reduced instance
        """
        return self.reduce_by_strategy(instance, DefaultStrategy)

    def reduce_by_non_native_json_strategy(self, instance: Any, strategy: Type[BaseNonNativeJsonStrategy]) -> JsonicReductionResult:
        reduced_instance = strategy.reduce(instance, self)
        reduced_instance[KELP_STRATEGY_KEY] = strategy.get_strategy_name()

        return reduced_instance

    def reduce_by_strategy(self, instance: Any, strategy: Type[BaseStrategy]) -> ReductionResult:
        """
        Reduce an instance using the specific strategy.

        :param instance: The instance to use_python_reduce
        :param strategy: The strategy to use (assumed to be fitting to the given instance already)
        :return: The reduced instance
        """
        if issubclass(strategy, BaseNonNativeJsonStrategy):
            return self.reduce_by_non_native_json_strategy(instance, strategy)
        else:
            return strategy.reduce(instance, self)


def restore_by_strategy_value(reduced_instance: JsonicReductionResult, unpickler: Unpickler) -> Any:
    """
    Restore reduced json-like objects using the strategy that's specified in their strategy key.

    :param reduced_instance: The reduced object to restore
    :param unpickler: The unpickler to be used for any inner members that should be restored as well.
    :return: The original object as was originally passed to Pickler's "use_python_reduce" function
    """

    strategy_name: Optional[str] = reduced_instance.get(KELP_STRATEGY_KEY, DictStrategy.get_strategy_name())

    strategy = get_strategy_by_name(strategy_name)
    if strategy is None:
        raise UnsupportedStrategy(f'Received an unsupported strategy name: {strategy_name}', strategy_name)

    return strategy.restore(reduced_instance, unpickler)


class Unpickler:
    reduced_type_to_restorer: dict[type, Callable[[ReductionResult, Unpickler], Any]] = {
        dict: restore_by_strategy_value,
        list: ListStrategy.restore,
        **{native_type: NullStrategy.restore for native_type in NATIVE_TYPES}
    }

    def unpickle(self, serialized_instance: str) -> Any:
        return self.restore(json.loads(serialized_instance))

    def restore(self, reduced_object: ReductionResult) -> Any:
        restorer = Unpickler.reduced_type_to_restorer.get(reduced_object.__class__)
        if restorer is None:
            raise UnpicklingError(f'Cannot restore object of type {reduced_object.__class__}.')

        return restorer(reduced_object, self)
