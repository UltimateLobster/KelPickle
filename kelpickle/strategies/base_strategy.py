from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING, Generic, Iterable
from abc import ABCMeta, abstractmethod

from kelpickle.common import Jsonable

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


T = TypeVar('T')


class BaseStrategy(Generic[T], metaclass=ABCMeta):
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
    def simplify(instance: T, pickler: Pickler) -> Jsonable:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def restore(simplified_object: Jsonable, unpickler: Unpickler) -> T:
        """
        Restore an instance that was simplified using the simplify method.
        """
        raise NotImplementedError()
