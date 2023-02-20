from __future__ import annotations

import json
from typing import Any, Optional, TypedDict
from pickle import DEFAULT_PROTOCOL

from bidict import bidict


from kelpickle.common import Jsonable, STRATEGY_KEY
from kelpickle.errors import RestorationReferenceCollision, ReductionReferenceCollision
from kelpickle.strategies.base_strategy import BaseStrategy, get_pickling_strategy_for, get_unpickling_strategy_for, get_strategy_named

ROOT_RELATIVE_KEY = "$ROOT"
REFERENCE_STRATEGY_NAME = "reference"


class ReferenceReductionResult(TypedDict):
    reference: str


class Pickler:
    PICKLE_PROTOCOL = DEFAULT_PROTOCOL

    def __init__(self) -> None:
        self.current_path: list[str] = []
        # Mapping between the id of encountered instances and their references in case we wish to reuse.
        self.__instances_references: bidict[int, str] = bidict({})
        self.__default_strategy: BaseStrategy = get_pickling_strategy_for(object)

    def _clean_cache(self) -> None:
        self.__instances_references.clear()

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

    def reduce(self, instance: Any, *, relative_key: str) -> Jsonable:
        """
        Reduce the given instance to a simplified representation of the steps to rebuild it.
        :param instance: The instance to use_python_reduce
        :param relative_key: This is relevant for the recursive nature of the function. This is an identifier for the
                             given instance that is unique among all of his sibling instances.

                             Ex. Consider the following object: {"outer1": {"inner1": 1, "inner2": 2}, "outer2": 2},
                             Upon reducing "outer1"'s value you will most likely need to call reduce on the value of
                             "inner1" as well as the value of "inner2". These 2 values will be called "sibling values"
                             since they lie exactly one level beneath the value of "outer1". When reducing them, you
                             will most likely need to pass "inner1"/"inner2" as the relative key. This is because they
                             will be unique among all of "outer1"'s direct calls to "reduce".

                             In other words. You need to make sure every direct call you make to reduce would be using
                             exactly 1 unique relative key for each value within the same level (it's ok for inner
                             recursive calls to "reduce" to reuse the same relative key).

        :return: The reduced instance
        """
        self.current_path.append(relative_key)
        try:
            instance_type = instance.__class__
            strategy = get_pickling_strategy_for(instance_type)
            if strategy.auto_generate_reduction_references:
                reduced_reference = self.attempt_reduce_by_reference(instance)
                if reduced_reference is not None:
                    # Instance was encountered previously and was therefore able to be reduced by reference.
                    return reduced_reference

            return self._use_strategy(instance, strategy=strategy)
        finally:
            self.current_path.pop()

    def _use_strategy(self, instance: Any, *, strategy: BaseStrategy) -> Jsonable:
        reduced_instance = strategy.reduce(instance=instance, pickler=self)
        if not strategy.is_json_native:
            reduced_instance[STRATEGY_KEY] = strategy.name

        return reduced_instance

    def default_reduce(self, instance: Any) -> Jsonable:
        """
        Reduce an instance using the default custom_strategies. This function is encouraged to be used by custom
        strategies that wish to "extend" the default functionality.

        :param instance: The instance to use_python_reduce
        :return: The reduced instance
        """
        return self._use_strategy(instance, strategy=self.__default_strategy)

    def attempt_reduce_by_reference(self, instance: Any) -> Optional[ReferenceReductionResult]:
        """
        Attempt to reduce an instance using the reference custom_strategies. If this is the first attempt, the instance
        will not be reduced and None will be returned. Otherwise, the result of the reduction by reference will be
        returned.

        :param instance: The reference that was generated for the instance
        :return: The reduced instance
        """
        instance_id = id(instance)
        existing_reference_name = self.__instances_references.get(instance_id)
        if existing_reference_name:
            return {"reference": existing_reference_name, STRATEGY_KEY: "reference"}

        current_reference = self.generate_current_reference()
        # While unlikely to be the case, we need to make sure the current reference is not referencing any other
        # instance. If so, this means something went wrong, and we have a collision. We would like to raise an exception
        # here instead of letting the user see the problem only upon unpickling.
        registered_instance_id = self.__instances_references.inverse.setdefault(current_reference, instance_id)
        if registered_instance_id is not instance_id:
            raise ReductionReferenceCollision(f"Instance id {instance_id} was trying to be recorded under the reference"
                                              f" name {current_reference} but it is already used for instance id "
                                              f"{registered_instance_id}", instance=instance)


class Unpickler:
    def __init__(self) -> None:
        self.current_path: list[str] = []
        self.__reference_to_restored_instances: dict[str, Any] = {}
        self.__partial_restores: list[tuple[BaseStrategy, Any]] = []

    def _clear_cache(self) -> None:
        self.__reference_to_restored_instances.clear()
        self.__partial_restores.clear()

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

    def restore(self, reduced_instance: Jsonable, *, relative_key: str) -> Any:
        """

        :param reduced_instance: The result of the "reduce" function
        :param relative_key: The counterpart of the "reduce" function's relative_key parameter.
                             Check the documentation for "reduce" for more information.
        :return:
        """
        self.current_path.append(relative_key)
        try:
            result = self.default_restore(reduced_instance)

            return result
        finally:
            self.current_path.pop()

    def default_restore(self, reduced_instance: Jsonable) -> Any:
        reduced_type = type(reduced_instance)
        if isinstance(reduced_instance, dict):
            strategy_name = reduced_instance.pop(STRATEGY_KEY, "dict")
            if strategy_name == "reference":
                return self._restore_reference(reduced_instance)
            strategy = get_strategy_named(strategy_name)
        else:
            strategy = get_unpickling_strategy_for(reduced_type)
        return self._restore_with_strategy(reduced_instance, strategy)

    def _restore_with_strategy(self, reduced_instance: Jsonable, strategy: BaseStrategy) -> Any:
        base_instance = strategy.restore_base(reduced_instance=reduced_instance, unpickler=self)
        self._record_reference(base_instance)
        strategy.restore_rest(reduced_instance=reduced_instance, unpickler=self, base_instance=base_instance)

    def _restore_reference(self, reduced_instance: ReferenceReductionResult):
        reference = reduced_instance["reference"]
        try:
            return self.__reference_to_restored_instances[reference]
        except KeyError as e:
            raise ValueError(
                f"Reference {reference} cannot be restored. The original object was not recorded yet."
            ) from e

    def _record_reference(self, instance: Any) -> None:
        current_reference = self.generate_current_reference()
        registered_instance = self.__reference_to_restored_instances.setdefault(current_reference, instance)

        if registered_instance is not instance:
            raise RestorationReferenceCollision(f"Cannot record instance {instance} under the reference "
                                                f"{current_reference}. The reference is already used by "
                                                f"{registered_instance}")


# Import all the builtin strategies in order to register them
from kelpickle.strategies.custom_strategies.bytes_strategy import BytesStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.date_strategy import DateStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.datetime_strategy import DatetimeStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.import_strategy import ImportStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.object_strategy import ObjectStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.set_strategy import SetStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.time_strategy import TimeStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.timedelta_strategy import TimeDeltaStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.tuple_strategy import TupleStrategy  # noqa: F401,E402
from kelpickle.strategies.custom_strategies.tzinfo_strategy import TzInfoStrategy  # noqa: F401,E402

from kelpickle.strategies.core_strategies import null_strategy  # noqa: F401,E402
from kelpickle.strategies.core_strategies import list_strategy  # noqa: F401,E402
from kelpickle.strategies.core_strategies import dict_strategy  # noqa: F401,E402
