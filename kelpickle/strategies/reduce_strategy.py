from __future__ import annotations

import sys
from pickle import DEFAULT_PROTOCOL
from typing import Any, TYPE_CHECKING, Optional, Iterable, Callable, TypeAlias

from kelpickle.strategies.base_strategy import BaseStrategy, T
from kelpickle.strategies.state_strategy import set_state, InstanceState
from kelpickle.strategies.import_strategy import restore_import_string

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


class ReduceError(ValueError):
    pass


def get_containing_module(import_string: str) -> Optional[str]:
    """
    This ugly ass function is a result of pickle supporting weird shit. When a __reduce__/__reduce_ex__ function returns
    a string, that is an import string to be used in the unpickling process. Only problem is, the import string is
    missing the module name. We literally have no way of finding the module name, therefore we need to bruteforce our
    way through 'sys.modules' until we find a module where this is importable (This is literally how pickle does it).

    :param import_string: The import string as returned from the __reduce__/__reduce_ex__ function.
    :return: The import string of the module containing the given object.
    """
    # We need to iterate over a copy of sys.modules because it might be edited as we iterate (additional modules may
    # be dynamically imported as getattr is called)
    for module_name, module in sys.modules.copy().items():
        current_parent = module
        try:
            for import_part in import_string.split("."):
                current_parent = getattr(current_parent, import_part)
        except AttributeError:
            # We didn't manage to import the entire object, that means this module is not the correct one.
            continue

        return module_name


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
            # The result is an import string that's missing the module part.
            containing_module = get_containing_module(reduce_result)
            if containing_module is None:
                raise ReduceError(f"Could not pickle object of type {type(instance)} with reduce result {reduce_result}"
                                  f", it is not importable from any module.")

            jsonified_instance['value'] = f"{containing_module}/{reduce_result}"
            return

        jsonified_result = [pickler.flatten(x) for x in reduce_result]
        jsonified_result.extend([None] * (6 - len(jsonified_result)))

        jsonified_instance['value'] = jsonified_result

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> T:
        flattened_reduce = jsonified_object['value']
        if isinstance(flattened_reduce, str):
            return restore_import_string(flattened_reduce)

        reduce_result = tuple(unpickler.restore(member) for member in flattened_reduce)
        return build_from_reduce(reduce_result)
