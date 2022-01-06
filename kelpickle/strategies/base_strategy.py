from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING
from abc import ABCMeta, abstractmethod

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


T = TypeVar('T')


class BaseStrategy(metaclass=ABCMeta):

    @staticmethod
    @abstractmethod
    def get_strategy_name() -> str:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def populate_json(instance: T, jsonified_instance: dict[str], pickler: Pickler) -> None:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> T:
        """
        Restore an instance that was jsonified using the populate_json method.
        """
        raise NotImplementedError()
