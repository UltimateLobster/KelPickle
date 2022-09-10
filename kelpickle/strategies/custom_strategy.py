from __future__ import annotations

from datetime import date, datetime, time, timedelta, tzinfo
from functools import wraps
from types import ModuleType, FunctionType, WrapperDescriptorType, MethodDescriptorType, GetSetDescriptorType, \
    MemberDescriptorType
from typing import Optional, Sequence, TypeVar, TYPE_CHECKING, TypedDict, TypeAlias, Callable, Type, Any, cast
from typing_extensions import NotRequired

from kelpickle.common import Json, KELP_STRATEGY_KEY
from kelpickle.errors import UnsupportedStrategy
from kelpickle._strategy_manager import (
    register_pickling_strategy as _register_internal_pickling_strategy,
    PicklingStrategy as InternalPicklingStrategy,
    UnpicklingStrategy as InternalUnpicklingStrategy,
    get_pickling_strategy as _get_internal_pickling_strategy,
    StrategyConflictError
)


ReductionResult = TypedDict("ReductionResult", {
    "kelp/strategy": NotRequired[str]
})

T = TypeVar('T')
ReducedT = TypeVar('ReducedT', bound=ReductionResult)

Reducer: TypeAlias = Callable[[T, 'Pickler'], ReducedT]
Restorer: TypeAlias = Callable[[ReducedT, 'Unpickler'], T]


# In order to avoid circular imports, we import the builtin strategies only after defining things core types they
# should be able to use
from kelpickle.strategies.custom.object_strategy import reduce_object, restore_object
from kelpickle.strategies.custom.set_strategy import reduce_set, restore_set
from kelpickle.strategies.custom.time_strategy import reduce_time, restore_time
from kelpickle.strategies.custom.timedelta_strategy import reduce_timedelta, restore_timedelta
from kelpickle.strategies.custom.tuple_strategy import reduce_tuple, restore_tuple
from kelpickle.strategies.custom.tzinfo_strategy import reduce_tzinfo, restore_tzinfo
from kelpickle.strategies.custom.bytes_strategy import reduce_bytes, restore_bytes
from kelpickle.strategies.custom.date_strategy import reduce_date, restore_date
from kelpickle.strategies.custom.datetime_strategy import reduce_datetime, restore_datetime
from kelpickle.strategies.dict_strategy import restore_dict
from kelpickle.strategies.custom.import_strategy import reduce_import, restore_import


if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class CustomPicklingStrategy(InternalPicklingStrategy[T, ReducedT]):
    def __init__(self, name: str, /, *,
                 reducer: Reducer[T, ReducedT],
                 supported_types: Sequence[Type[T]],
                 auto_generate_references: bool = True,
                 ):
        super().__init__(reducer=reducer, auto_generate_references=auto_generate_references, supported_types=supported_types)
        self.name = name

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.name}>"


class CustomUnpicklingStrategy(InternalUnpicklingStrategy[ReducedT, T]):
    def __init__(self, name: str, /, *,
                 restorer: Restorer[ReducedT, T]
                 ):
        super().__init__(restorer=restorer, supported_types=[])
        self.name = name

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.name}>"


__name_to_strategy: dict[str, CustomUnpicklingStrategy] = {}


def register_pickling_strategy(strategy: CustomPicklingStrategy, consider_subclasses: bool = False) -> None:
    _register_internal_pickling_strategy(strategy, consider_subclasses=consider_subclasses)


def register_unpickling_strategy(strategy: CustomUnpicklingStrategy) -> None:
    if strategy.name in __name_to_strategy and __name_to_strategy[strategy.name] is not strategy:
        raise StrategyConflictError(f"Cannot configure {strategy.name} strategies. It has been already configured.")

    __name_to_strategy[strategy.name] = strategy


def __wrap_custom_reducer(reducer: Reducer[T, ReducedT], name: str) -> Reducer[T, ReducedT]:
    """
    Wraps a custom reducer with functionality that is common to every custom reducer
    """
    @wraps(reducer)
    def wrapped(instance: T, pickler: Pickler) -> ReducedT:
        result = reducer(instance, pickler)
        result[KELP_STRATEGY_KEY] = name

        return result
    return wrapped


def register_strategy(
        name: str, /, *,
        reducer: Reducer[T, ReducedT],
        restorer: Restorer[ReducedT, T],
        supported_types: Sequence[Type[T]],
        auto_generate_references: bool = True,
        consider_subclasses: bool = False
) -> None:
    pickling_strategy = CustomPicklingStrategy(
        name,
        reducer=__wrap_custom_reducer(reducer, name),
        supported_types=supported_types,
        auto_generate_references=auto_generate_references,
    )
    register_pickling_strategy(pickling_strategy, consider_subclasses=consider_subclasses)

    unpickling_strategy = CustomUnpicklingStrategy(
        name,
        restorer=restorer,
    )
    register_unpickling_strategy(unpickling_strategy)


def __get_pickling_strategy(type_: Type[T]) -> Optional[CustomPicklingStrategy[T, ReducedT]]:
    return cast(Optional[CustomPicklingStrategy[T, ReducedT]], _get_internal_pickling_strategy(type_))


def __get_unpickling_strategy(name: str) -> Optional[CustomUnpicklingStrategy]:
    return __name_to_strategy.get(name)


def __register_builtin_strategies():
    register_strategy(
        "base64",
        reducer=reduce_bytes,
        restorer=restore_bytes,
        supported_types=[bytes]
    )

    register_strategy(
        "date",
        reducer=reduce_date,
        restorer=restore_date,
        supported_types=[date]
    )

    register_strategy(
        "datetime",
        reducer=reduce_datetime,
        restorer=restore_datetime,
        supported_types=[datetime]
    )

    register_strategy(
        "import",
        # Imports by definition are kinda like references, therefore no need to save references for these
        reducer=reduce_import,
        restorer=restore_import,
        supported_types=[
            type,
            ModuleType,
            FunctionType,
            WrapperDescriptorType,
            MethodDescriptorType,
            GetSetDescriptorType,
            MemberDescriptorType
        ],
        auto_generate_references=False,
    )

    register_strategy(
        "object",
        reducer=reduce_object,
        restorer=restore_object,
        supported_types=[object],
        consider_subclasses=True,
    )

    register_strategy(
        "set",
        reducer=reduce_set,
        restorer=restore_set,
        supported_types=[set]
    )

    register_strategy(
        "time",
        reducer=reduce_time,
        restorer=restore_time,
        supported_types=[time]
    )

    register_strategy(
        "timedelta",
        reducer=reduce_timedelta,
        restorer=restore_timedelta,
        supported_types=[timedelta]
    )

    register_strategy(
        "tuple",
        reducer=reduce_tuple,
        restorer=restore_tuple,
        supported_types=[tuple]
    )

    register_strategy(
        "tzinfo",
        reducer=reduce_tzinfo,
        restorer=restore_tzinfo,
        supported_types=[tzinfo],
        consider_subclasses=True
    )


__register_builtin_strategies()


def restore_with_custom_strategy(reduced_instance: ReductionResult | Json, unpickler: Unpickler) -> Any:
    """
    Restore objects that were reduced into json-like dicts using the custom strategies that's specified in their
    strategies key. If the strategies key does not exist, restore as a dict.

    :param reduced_instance: The reduced object to restore
    :param unpickler: The unpickler to be used for any inner members that should be restored as well.
    :return: The original object as was originally passed to Pickler's "reduce" function
    """
    strategy_name: Optional[str] = reduced_instance.get(KELP_STRATEGY_KEY)
    if strategy_name is None:
        return restore_dict(cast(Json, reduced_instance), unpickler)

    strategy = __get_unpickling_strategy(strategy_name)
    if strategy is None:
        raise UnsupportedStrategy(f'Received an unsupported strategies name: {strategy_name}', strategy_name)

    return strategy.restorer(reduced_instance, unpickler)
