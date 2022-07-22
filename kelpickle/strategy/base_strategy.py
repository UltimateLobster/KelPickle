from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING, Generic, Iterable, TypedDict, TypeAlias
from abc import ABCMeta, abstractmethod

from kelpickle.common import Jsonable, Json, JsonNative

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


_OriginalType = TypeVar('_OriginalType')
_ReducedInstanceType = TypeVar('_ReducedInstanceType', bound=Jsonable)


JsonicReductionResult = TypedDict("JsonicReductionResult", {
    "kelp/strategy": str
}, total=False)
ReductionResult: TypeAlias = JsonicReductionResult | list | JsonNative


class BaseStrategy(Generic[_OriginalType, _ReducedInstanceType], metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_strategy_name() -> str:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def get_supported_types() -> Iterable[type]:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def reduce(
            instance: _OriginalType,
            pickler: Pickler
    ) -> ReductionResult:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def restore(
            reduced_object: ReductionResult,
            unpickler: Unpickler
    ) -> _OriginalType:
        """
        Restore an instance that was reduced using the pyreduce method.
        """
        raise NotImplementedError()


_NonNativeReducedType = TypeVar('_NonNativeReducedType', bound=Json)


class BaseNonNativeJsonStrategy(Generic[_OriginalType, _NonNativeReducedType], BaseStrategy[_OriginalType, _NonNativeReducedType], metaclass=ABCMeta):
    pass
