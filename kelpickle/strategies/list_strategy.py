from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

from kelpickle.strategies.base_strategy import BaseStrategy
from kelpickle.common import JsonList


class ListStrategy(BaseStrategy[list]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'list'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [list]

    @staticmethod
    def simplify(instance: list, pickler: Pickler) -> JsonList:
        return [pickler.simplify(member) for member in instance]

    @staticmethod
    def restore(simplified_object: JsonList, unpickler: Unpickler) -> list:
        return [unpickler.restore(member) for member in simplified_object]
