from __future__ import annotations
from typing import Sequence, TypeVar, TYPE_CHECKING, TypeAlias, Callable, Type, Generic, Optional

from kelpickle.common import JsonNative, Json

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

T = TypeVar('T')
ReducedT = TypeVar('ReducedT', bound=list | JsonNative | Json)

Reducer: TypeAlias = Callable[[T, 'Pickler'], ReducedT]
Restorer: TypeAlias = Callable[[ReducedT, 'Unpickler'], T]


class PicklingStrategy(Generic[T, ReducedT]):
    def __init__(self, *,
                 reducer: Reducer[T, ReducedT],
                 auto_generate_references: bool,
                 supported_types: Sequence[Type[T]]
                 ):
        self.reducer = reducer
        self.auto_generate_references = auto_generate_references
        self.supported_types = supported_types

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.supported_types}>"


class UnpicklingStrategy(Generic[ReducedT, T]):
    def __init__(self, *,
                 restorer: Restorer[ReducedT, T],
                 supported_types: Sequence[Type[T]]
                 ):
        self.restorer = restorer
        self.supported_types = supported_types

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.supported_types}>"


class StrategyConflictError(ValueError):
    pass


class UnsupportedPicklingType(TypeError):
    pass


__type_to_pickling_strategy: dict[type, PicklingStrategy] = {}
__superclass_to_pickling_strategy: dict[type, PicklingStrategy] = {}
__type_to_unpickling_strategy: dict[type, UnpicklingStrategy] = {}


def register_pickling_strategy(strategy: PicklingStrategy, *, consider_subclasses: bool) -> None:
    for type_ in strategy.supported_types:
        if type_ in __type_to_pickling_strategy and __type_to_pickling_strategy[type_] is not strategy:
            raise StrategyConflictError(f"Cannot configure type {type_} for reducer {strategy}. It is "
                                        f"already configured to {__type_to_pickling_strategy[type_]}")
        __type_to_pickling_strategy[type_] = strategy
        if consider_subclasses:
            if type_ in __superclass_to_pickling_strategy and __superclass_to_pickling_strategy[type_] is not strategy:
                raise StrategyConflictError(f"Cannot configure type {type_} for reducer {strategy}. It is "
                                            f"already configured to {__superclass_to_pickling_strategy[type_]}")
            __superclass_to_pickling_strategy[type_] = strategy


def register_unpickling_strategy(strategy: UnpicklingStrategy) -> None:
    for type_ in strategy.supported_types:
        if type_ in __type_to_unpickling_strategy and __type_to_unpickling_strategy[type_] is not strategy:
            raise StrategyConflictError(f"Cannot configure type {type_} for reducer {strategy}. It is "
                                        f"already configured to {__type_to_unpickling_strategy[type_]}")
        __type_to_unpickling_strategy[type_] = strategy


def register_strategy(
        reducer: Reducer[T, ReducedT],
        restorer: Restorer[ReducedT, T],
        auto_generate_references: bool,
        supported_types: Sequence[Type[T]],
        consider_base_classes: bool = False,
) -> None:
    pickling_strategy = PicklingStrategy(
        reducer=reducer,
        auto_generate_references=auto_generate_references,
        supported_types=supported_types
    )
    register_pickling_strategy(pickling_strategy, consider_subclasses=consider_base_classes)

    unpickling_strategy = UnpicklingStrategy(
        restorer=restorer,
        supported_types=supported_types
    )
    register_unpickling_strategy(unpickling_strategy)


def get_pickling_strategy(type_: Type[T]) -> PicklingStrategy[T, ReducedT]:
    strategy = __type_to_pickling_strategy.get(type_)
    if strategy is not None:
        return strategy

    for base_class in type_.mro()[1:]:
        strategy = __superclass_to_pickling_strategy.get(base_class)
        if strategy is not None:
            return strategy

    raise UnsupportedPicklingType(f'Type {type_} has no viable strategy available to use')


def get_unpickling_strategy(type_: Type[T]) -> UnpicklingStrategy[ReducedT, T]:
    return __type_to_unpickling_strategy[type_]
