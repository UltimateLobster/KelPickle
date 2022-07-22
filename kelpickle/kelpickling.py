from __future__ import annotations

import json

from typing import Type, Any, Callable, Optional
from kelpickle.common import NATIVE_TYPES, KELP_STRATEGY_KEY
from kelpickle.strategy.base_strategy import BaseStrategy, ReductionResult, JsonicReductionResult, \
    BaseNonNativeJsonStrategy
from kelpickle.strategy.state_strategy import StateStrategy
from kelpickle.strategy.pyreduce_strategy import PyReduceStrategy
from kelpickle.strategy.null_strategy import NullStrategy
from kelpickle.strategy.list_strategy import ListStrategy
from kelpickle.strategy.dict_strategy import DictStrategy
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
        """
        serialize the given python object.

        :param instance: The instance to serialize
        :return: The serialized instance
        """
        return json.dumps(self.reduce(instance))

    def reduce(self, instance: Any) -> ReductionResult:
        """
        Reduce the given instance to a simplified representation of the steps to rebuild it.
        :param instance: The instance to pyreduce
        :return: The reduced instance
        """
        instance_type = instance.__class__
        strategy = get_strategy_by_type(instance_type)
        if strategy is None:
            return Pickler.default_reduce(instance, self)

        return self.reduce_by_strategy(instance, strategy)

    def reduce_by_non_native_json_strategy(self, instance: Any, strategy: Type[BaseNonNativeJsonStrategy]) -> JsonicReductionResult:
        reduced_instance = strategy.reduce(instance, self)
        reduced_instance[KELP_STRATEGY_KEY] = strategy.get_strategy_name()

        return reduced_instance

    def reduce_by_strategy(self, instance: Any, strategy: Type[BaseStrategy]) -> ReductionResult:
        """
        Reduce an instance using the specific strategy.

        :param instance: The instance to pyreduce
        :param strategy: The strategy to use (assumed to be fitting to the given instance already)
        :return: The reduced instance
        """
        if issubclass(strategy, BaseNonNativeJsonStrategy):
            return self.reduce_by_non_native_json_strategy(instance, strategy)
        else:
            return strategy.reduce(instance, self)

    @staticmethod
    def default_reduce(instance: Any, pickler: Pickler) -> ReductionResult:
        """
        The default pyreduce method that is used if no strategy is found for the type of the instance.

        # TODO: Convert to Cython.
        Notice this function is static method even though it receives a Pickler instance. This is done because in the
        future I'm planning to convert the code to use Cython which will c implemented classes to have static methods
        if they are to be accessed dynamically.

        :param instance: The instance to pyreduce
        :param pickler: The pickler that is used to pyreduce the instance
        :return: The reduced object
        """
        instance_type = instance.__class__
        if instance_type.__reduce_ex__ == DEFAULT_REDUCE_EX and instance_type.__reduce__ == DEFAULT_REDUCE:
            # We have no custom implementation of __reduce__/__reduce_ex__. We may use the state shortcut instead.
            strategy = StateStrategy
        else:
            strategy = PyReduceStrategy

        return pickler.reduce_by_strategy(instance, strategy)


def restore_by_strategy_value(reduced_instance: JsonicReductionResult, unpickler: Unpickler) -> Any:
    """
    Restore reduced json-like objects using the strategy that's specified in their strategy key.

    :param reduced_instance: The reduced object to restore
    :param unpickler: The unpickler to be used for any inner members that should be restored as well.
    :return: The original object as was originally passed to Pickler's "pyreduce" function
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
