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


ROOT_RELATIVE_KEY = "$ROOT"
REFERENCE_STRATEGY_NAME = "reference"


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

    def __init__(self):
        self.current_path = []
        # Mapping between the id of encountered instances and their references in case we wish to reuse.
        self.instances_references: dict[int, str] = {}

    def _clean_cache(self):
        self.instances_references = {}

    def generate_current_reference(self) -> str:
        """
        Generate a unique reference for the current path.

        :return: The unique reference
        """
        # TODO: Change the logic so parts of the path that contain the separator will somehow be escaped
        return "->".join(self.current_path)

    def pickle(self, instance: Any) -> str:
        """
        serialize the given python object.

        :param instance: The instance to serialize
        :return: The serialized instance
        """
        result = json.dumps(self.reduce(instance, relative_key=ROOT_RELATIVE_KEY))
        self._clean_cache()

        return result

    def reduce(self, instance: Any, *, relative_key: str) -> ReductionResult:
        """
        Reduce the given instance to a simplified representation of the steps to rebuild it.
        :param instance: The instance to use_python_reduce
        :param relative_key: This is relevant for the recursive nature of the function. This is an identifier for the
                             given instance that is unique among all of his sibling instances.

                             Ex. Consider the following object: {"outer1": {"inner1": 1, "inner2": 2}, "outer2": 2},
                             Upon reducing "outer1"'s value you will most likely need to call reduce on the value of
                             "inner1" as well as the value of "inner2". These 2 values will be called "sibling values"
                             since they lie exactly one level beneith the value of "outer1". When reducing them, you
                             will most likely need to pass "inner1"/"inner2" as the relative key. This is because they
                             will be unique among all of "outer1"'s direct calls to "reduce".

                             In other words. You need to make sure every direct call you make to reduce would be using
                             exactly 1 unique relative key for each value within the same level (it's ok for inner
                             recursive calls to "reduce" to reuse the same relative key).

        :return: The reduced instance
        """
        self.current_path.append(relative_key)
        try:
            instance_id = id(instance)
            instance_reference = self.instances_references.get(instance_id)
            if instance_reference is not None:
                return self._reduce_by_reference(instance_reference)

            instance_type = instance.__class__
            strategy = get_strategy_by_type(instance_type)
            if strategy is None:
                return self.default_reduce(instance)

            return self.reduce_by_strategy(instance, strategy)
        finally:
            self.current_path.pop()

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
        if strategy.should_auto_generate_references():
            instance_reference = self.generate_current_reference()
            self.instances_references[id(instance)] = instance_reference

        if issubclass(strategy, BaseNonNativeJsonStrategy):
            return self.reduce_by_non_native_json_strategy(instance, strategy)
        else:
            return strategy.reduce(instance, self)

    @staticmethod
    def _reduce_by_reference(instance_reference: str) -> ReductionResult:
        """
        Reduce an instance using the reference strategy.

        :param instance_reference: The reference that was generated for the instance
        :return: The reduced instance
        """
        return {KELP_STRATEGY_KEY: REFERENCE_STRATEGY_NAME, "reference": instance_reference}


def restore_by_strategy_value(reduced_instance: JsonicReductionResult, unpickler: Unpickler) -> Any:
    """
    Restore reduced json-like objects using the strategy that's specified in their strategy key.

    :param reduced_instance: The reduced object to restore
    :param unpickler: The unpickler to be used for any inner members that should be restored as well.
    :return: The original object as was originally passed to Pickler's "use_python_reduce" function
    """

    strategy_name: Optional[str] = reduced_instance.get(KELP_STRATEGY_KEY, DictStrategy.get_strategy_name())

    if strategy_name == REFERENCE_STRATEGY_NAME:
        return unpickler.restore_by_reference(reduced_instance["reference"])

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

    def __init__(self):
        self.current_path = []
        self.reference_to_restored_instances: dict[str, Any] = {}

    def _clear_cache(self):
        self.reference_to_restored_instances = {}

    def generate_current_reference(self) -> str:
        """
        Generate a unique reference for the current path.

        :return: The unique reference
        """
        # TODO: Change the logic so parts of the path that contain the separator will somehow be escaped
        return "->".join(self.current_path)

    def unpickle(self, serialized_instance: str) -> Any:
        result = self.restore(json.loads(serialized_instance), relative_key=ROOT_RELATIVE_KEY)
        self._clear_cache()

        return result

    def restore(self, reduced_object: ReductionResult, *, relative_key: str) -> Any:
        """

        :param reduced_object: The result of the "reduce" function
        :param relative_key: The counterpart of the "reduce" function's relative_key parameter.
                             Check the documentation for "reduce" for more information.
        :return:
        """
        self.current_path.append(relative_key)
        try:
            result = self.default_restore(reduced_object)
            self.reference_to_restored_instances[self.generate_current_reference()] = result

            return result
        finally:
            self.current_path.pop()

    def restore_by_reference(self, reference: str) -> Any:
        """
        Restore an instance using the reference strategy.

        :param reference: The reference that was generated for the instance
        :return: The restored instance
        """
        return self.reference_to_restored_instances[reference]

    # TODO: This desperately needs a better name
    def default_restore(self, reduced_object: ReductionResult) -> Any:
        restorer = Unpickler.reduced_type_to_restorer.get(reduced_object.__class__)
        if restorer is None:
            raise UnpicklingError(f'Cannot restore object of type {reduced_object.__class__}.')

        return restorer(reduced_object, self)
