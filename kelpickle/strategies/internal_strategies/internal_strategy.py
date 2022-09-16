from __future__ import annotations

from dataclasses import dataclass
from typing import Type, Callable, TypeAlias, TYPE_CHECKING, Any

from kelpickle.common import Jsonable

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


Reducer: TypeAlias = Callable[[Any, 'Pickler'], Jsonable]
Restorer: TypeAlias = Callable[[Jsonable, 'Unpickler'], Any]


@dataclass(kw_only=True)
class PicklingStrategy:
    reduce_function: Reducer
    auto_generate_references: bool


@dataclass(kw_only=True)
class UnpicklingStrategy:
    restore_function: Restorer


class StrategyConflictError(ValueError):
    pass


class UnsupportedPicklingType(TypeError):
    pass


__type_to_pickling_strategy: dict[type, PicklingStrategy] = {}
__superclass_to_pickling_strategy: dict[type, PicklingStrategy] = {}
__type_to_unpickling_strategy: dict[type, UnpicklingStrategy] = {}


def register_pickling_strategy(
        pickling_strategy: PicklingStrategy, *,
        type_to_pickle: type,
        consider_subclasses: bool,
) -> None:
    if __type_to_pickling_strategy.get(type_to_pickle) is not None:
        raise StrategyConflictError(f"Cannot configure type {type_to_pickle} for reducer {pickling_strategy}. It is "
                                    f"already configured to {__type_to_pickling_strategy[type_to_pickle]}")
    __type_to_pickling_strategy[type_to_pickle] = pickling_strategy

    if consider_subclasses:
        if __superclass_to_pickling_strategy.get(type_to_pickle) is not None:
            raise StrategyConflictError(f"Cannot configure type {type_to_pickle} for reducer {pickling_strategy}. It "
                                        f"is already configured to {__superclass_to_pickling_strategy[type_to_pickle]}")
        __superclass_to_pickling_strategy[type_to_pickle] = pickling_strategy


def register_unpickling_strategy(
        unpickling_strategy: UnpicklingStrategy, *,
        type_to_unpickle: type
) -> None:
    if __type_to_unpickling_strategy.get(type_to_unpickle) is not None:
        raise StrategyConflictError(f"Cannot configure type {type_to_unpickle} for reducer {unpickling_strategy}. It "
                                    f"is already configured to {__type_to_unpickling_strategy[type_to_unpickle]}")
    __type_to_unpickling_strategy[type_to_unpickle] = unpickling_strategy


def get_pickling_strategy(instance_type: type) -> PicklingStrategy:
    strategy = __type_to_pickling_strategy.get(instance_type)
    if strategy is not None:
        return strategy

    for base_class in instance_type.mro()[1:]:
        strategy = __superclass_to_pickling_strategy.get(base_class)
        if strategy is not None:
            return strategy

    raise UnsupportedPicklingType(f'Type {instance_type} has no viable strategy available to use')


def get_unpickling_strategy(reduced_type: Type[Jsonable]) -> UnpicklingStrategy:
    return __type_to_unpickling_strategy[reduced_type]
