from functools import wraps
from typing import TypeVar, Callable, Generic, Sequence, Type, TYPE_CHECKING, ParamSpec, Optional, cast, Any, TypedDict

from kelpickle.strategies.internal_strategies.internal_strategy import (
    PicklingStrategy,
    UnpicklingStrategy,
    register_pickling_strategy,
    StrategyConflictError,
    Reducer,
    Restorer
)
from kelpickle.strategies.internal_strategies.dict_strategy import restore_dict
from kelpickle.common import Json, KELP_STRATEGY_KEY
from kelpickle.errors import UnsupportedStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

P = ParamSpec('P')
T = TypeVar('T')
ReducedT = TypeVar('ReducedT', bound=Json)

__name_to_unpickling_strategy: dict[str, UnpicklingStrategy] = {}

CustomReductionResult = TypedDict('CustomReductionResult', {
    KELP_STRATEGY_KEY: str
})


class Strategy(Generic[T, ReducedT]):
    @staticmethod
    def reduce(instance: T, pickler: 'Pickler') -> ReducedT:
        raise NotImplementedError()

    @staticmethod
    def restore(reduced_object: ReducedT, unpickler: 'Unpickler') -> T:
        raise NotImplementedError()


def __with_strategy_key(reduce_function: Callable[P, dict], strategy_name: str) -> Callable[P, CustomReductionResult]:
    """
    Wraps a custom_strategies reducer with functionality that is common to every custom_strategies reducer
    """
    @wraps(reduce_function)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> CustomReductionResult:
        result = reduce_function(*args, **kwargs)
        result[KELP_STRATEGY_KEY] = strategy_name

        return result
    return wrapped


def restore_with_non_json_strategy(reduced_instance: Json, unpickler: 'Unpickler') -> Any:
    """
    Restore objects that were reduced into json-like dicts. If a strategy key exists, the corresponding strategy will
    be used in order to restore the object. If the key does not exist, the dict strategy will be used instead.

    :param reduced_instance: The reduced object to restore
    :param unpickler: The unpickler to be used for any inner members that should be restored as well.
    :return: The original object as was originally passed to Pickler's "reduce" function
    """
    strategy_name: Optional[str] = reduced_instance.get(KELP_STRATEGY_KEY)
    if strategy_name is None:
        return restore_dict(cast(Json, reduced_instance), unpickler)

    unpickling_strategy = __name_to_unpickling_strategy.get(strategy_name)
    if unpickling_strategy is None:
        raise UnsupportedStrategy(f'Received an unsupported strategies name: {strategy_name}', strategy_name)

    return unpickling_strategy.restore_function(reduced_instance, unpickler)


def register_strategy(
        strategy_name: str, *,
        supported_types: Sequence[Type[T]] | Type[T],
        auto_generate_references: bool = True,
        consider_subclasses: bool = False,
) -> Callable[[Type[Strategy]], Type[Strategy]]:
    if isinstance(supported_types, type):
        supported_types = [supported_types]

    def decorator(cls: Type[Strategy]) -> Type[Strategy]:
        _register_pickling_strategy_name(
            strategy_name,
            reduce_function=cls.reduce,
            supported_types=supported_types,
            auto_generate_references=auto_generate_references,
            consider_subclasses=consider_subclasses
        )
        _register_unpickling_strategy_name(strategy_name, restore_function=cls.restore)
        return cls

    return decorator


def _register_pickling_strategy_name(
        strategy_name: str, *,
        reduce_function: Reducer,
        supported_types: list[type],
        auto_generate_references: bool,
        consider_subclasses: bool,
) -> None:
    pickling_strategy = PicklingStrategy(reduce_function=__with_strategy_key(reduce_function, strategy_name),
                                         auto_generate_references=auto_generate_references)
    for type_ in supported_types:
        register_pickling_strategy(pickling_strategy, type_to_pickle=type_, consider_subclasses=consider_subclasses)


def _register_unpickling_strategy_name(
        strategy_name: str, *,
        restore_function: Restorer
) -> None:
    if __name_to_unpickling_strategy.get(strategy_name) is not None:
        raise StrategyConflictError(f"Cannot configure {strategy_name} strategies. It has been already configured.")
    __name_to_unpickling_strategy[strategy_name] = UnpicklingStrategy(restore_function=restore_function)
