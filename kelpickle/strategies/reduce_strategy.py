from __future__ import annotations

from pickle import DEFAULT_PROTOCOL
from typing import Any, TYPE_CHECKING, Optional, Iterable, Callable, TypeAlias

from kelpickle.strategies.base_strategy import BaseStrategy, T
from kelpickle.strategies.state_strategy import set_state, InstanceState

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


ReduceResult: TypeAlias = str | tuple[
    Callable,
    Iterable,
    Optional[InstanceState | Any],
    Optional[Iterable],
    Optional[Iterable[tuple[str, Any]]],
    Optional[Callable[[Any, InstanceState], None]]
]


class UnreducableObject(ValueError):
    pass


def reduce(instance: T) -> ReduceResult:
    if reduce_func := getattr(instance, "__reduce_ex__", None):
        return reduce_func(DEFAULT_PROTOCOL)

    if reduce_func := getattr(instance, "__reduce__", None):
        return reduce_func()

    raise UnreducableObject(f'Instance of type {type(instance)} cannot be pickled. It does not implement the reduce '
                            f'protocol.', instance)


def build_from_reduce(reduce_result: ReduceResult) -> Any:
    """
    Build an instance from the result of a previously called __reduce__/__reduce_ex__.

    Explanation about reduce:
       # TODO: Add explanation here.

    :param reduce_result: The result of __reduce__/__reduce_ex__
    :return: The newly created instance.
    """
    # TODO: Add support for string reduce results
    callable_, args, state, list_items, dict_items, custom_set_state = reduce_result

    # Step 1: Create the instance
    instance = callable_(*args)

    # Step 2: Add items
    if list_items is not None:
        try:
            extend = instance.extend
        except AttributeError:
            # If object did not implement the 'extend' method, fallback on 'append' method.
            append = instance.append
            for item in list_items:
                append(item)

        else:
            extend(list_items)

    # Step 3: Set items
    if dict_items is not None:
        for key, value in dict_items:
            instance[key] = value

    # Step 4: Set the new state
    if state is not None:
        if custom_set_state:
            custom_set_state(instance, state)
        else:
            set_state(instance, state)

    return instance


class ReduceStrategy(BaseStrategy):
    @staticmethod
    def get_strategy_name() -> str:
        return 'reduce'

    @staticmethod
    def populate_json(instance: T, jsonified_instance: dict[str], pickler: Pickler) -> None:
        reduce_result = reduce(instance)
        if isinstance(reduce_result, str):
            jsonified_instance['value'] = reduce_result

        jsonified_result = [pickler.flatten(x) for x in reduce_result]
        jsonified_result.extend([None] * (6 - len(jsonified_result)))

        jsonified_instance['value'] = jsonified_result

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> T:
        flattened_reduce = jsonified_object['value']
        reduce_result = unpickler.restore(flattened_reduce)

        return build_from_reduce(reduce_result)
