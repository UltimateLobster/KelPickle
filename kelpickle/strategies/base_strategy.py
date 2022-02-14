from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING, Generic
from abc import ABCMeta, abstractmethod

from kelpickle.common import Json

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


T = TypeVar('T')


class BaseStrategy(Generic[T], metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def get_strategy_name() -> str:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def flatten(instance: T, pickler: Pickler) -> Json:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def restore(jsonified_object: Json, unpickler: Unpickler) -> T:
        """
        Restore an instance that was jsonified using the populate_json method.
        """
        raise NotImplementedError()
