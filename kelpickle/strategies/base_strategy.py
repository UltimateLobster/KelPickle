from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Generic, TypeVar, final, Type, Callable, Optional, TYPE_CHECKING, Sequence

from kelpickle.common import Jsonable
from kelpickle.errors import StrategyConflictError, UnsupportedPicklingType

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

T = TypeVar('T')
ReducedT = TypeVar('ReducedT', bound=Jsonable)


__type_to_strategy: dict[type, BaseStrategy] = {}
__superclass_to_pickling_strategy: dict[type, BaseStrategy] = {}
__name_to_strategy: dict[str, BaseStrategy] = {}
__reduced_type_to_strategy: dict[type, BaseStrategy] = {}


class BaseStrategy(Generic[T, ReducedT], metaclass=ABCMeta):
    @final
    def __init__(
            self, *,
            name: str,
            auto_generate_reduction_references: bool,
            supported_types: Sequence[Type[T]],
            consider_subclasses: bool,
            is_json_native: bool,
    ):
        self.name = name
        self.auto_generate_reduction_references = auto_generate_reduction_references
        self.supported_types = supported_types
        self.consider_subclasses = consider_subclasses
        self.is_json_native = is_json_native

    @abstractmethod
    def reduce(self, *, instance: T, pickler: Pickler) -> ReducedT:
        raise NotImplementedError()

    @abstractmethod
    def restore_base(self, *, reduced_instance: ReducedT, unpickler: Unpickler) -> T:
        raise NotImplementedError()

    def restore_rest(self, *, reduced_instance: ReducedT, unpickler: Unpickler, base_instance: T) -> None:
        return base_instance


_StrategyT = TypeVar('_StrategyT', bound=Type[BaseStrategy])


def _register_strategy(
        *,
        name: str,
        auto_generate_reduction_references: bool,
        supported_types: Sequence[type],
        consider_subclasses: bool,
        reduced_type: Optional[type] = None,
        is_json_native: bool,
) -> Callable:
    def class_decorator(strategy_class: _StrategyT) -> _StrategyT:
        strategy = strategy_class(
            name=name,
            auto_generate_reduction_references=auto_generate_reduction_references,
            supported_types=supported_types,
            consider_subclasses=consider_subclasses,
            is_json_native=is_json_native
        )

        if __name_to_strategy.get(name) is not None:
            raise StrategyConflictError(f"Cannot register strategy with name {name}. Name is already taken by "
                                        f"{__name_to_strategy[name]}")

        __name_to_strategy[name] = strategy

        if reduced_type is not None:
            if __reduced_type_to_strategy.get(reduced_type) is not None:
                raise StrategyConflictError(f"Cannot configure type {reduced_type} for strategy {strategy}. It "
                                            f"is already configured to {__reduced_type_to_strategy[reduced_type]}")
            __reduced_type_to_strategy[reduced_type] = strategy

        for supported_type in supported_types:
            if __type_to_strategy.get(supported_type) is not None:
                raise StrategyConflictError(f"Cannot configure type {supported_type} to strategy {strategy_class.__name__}."
                                            f" It is already configured to strategy "
                                            f"{__type_to_strategy[supported_type].__class__.__name__}")
            __type_to_strategy[supported_type] = strategy

            if consider_subclasses:
                if __superclass_to_pickling_strategy.get(supported_type) is not None:
                    raise StrategyConflictError(f"Cannot configure type {supported_type} for strategy {strategy}. It "
                                                f"is already configured to {__superclass_to_pickling_strategy[supported_type]}")
                __superclass_to_pickling_strategy[supported_type] = strategy

        return strategy_class

    return class_decorator


def register_strategy(
        *,
        name: str,
        auto_generate_reduction_references: bool,
        supported_types: type | Sequence[type],
        consider_subclasses: bool = False,
) -> Callable:
    if isinstance(supported_types, type):
        supported_types = (supported_types, )
    return _register_strategy(
        name=name,
        auto_generate_reduction_references=auto_generate_reduction_references,
        supported_types=supported_types,
        consider_subclasses=consider_subclasses,
        is_json_native=False
    )


def register_core_strategy(
        *,
        auto_generate_reduction_references: bool,
        supported_type: type,
) -> Callable:
    return _register_strategy(
        name=str(supported_type),
        auto_generate_reduction_references=auto_generate_reduction_references,
        supported_types=(supported_type,),
        consider_subclasses=False,
        reduced_type=supported_type,
        is_json_native=True
    )


def get_pickling_strategy_for(instance_type: type, /) -> BaseStrategy:
    strategy = __type_to_strategy.get(instance_type)
    if strategy is not None:
        return strategy

    for base_class in instance_type.mro()[1:]:
        strategy = __superclass_to_pickling_strategy.get(base_class)
        if strategy is not None:
            return strategy

    raise UnsupportedPicklingType(f'Type {instance_type} has no viable strategy available to use')


def get_unpickling_strategy_for(reduced_type: Type[Jsonable], /) -> BaseStrategy:
    return __reduced_type_to_strategy[reduced_type]


def get_strategy_named(strategy_name: str, /) -> BaseStrategy:
    return __name_to_strategy[strategy_name]
