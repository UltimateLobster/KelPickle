from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, TypeVar, Generic
from kelpickle.common import JsonNative, NATIVE_TYPES
from kelpickle.strategy.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


Native = TypeVar("Native", bound=JsonNative)


class NullStrategy(Generic[Native], BaseStrategy[Native, Native]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'null'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return NATIVE_TYPES

    @staticmethod
    def reduce(instance: Native, pickler: Pickler) -> Native:
        return instance

    @staticmethod
    def restore(reduced_object: Native, unpickler: Unpickler) -> Native:
        return reduced_object
