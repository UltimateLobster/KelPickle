from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler

from kelpickle.strategies.base_strategy import BaseStrategy
from kelpickle.common import JsonList


class ListStrategy(BaseStrategy[list]):
    @staticmethod
    def flatten(instance: list, pickler: Pickler) -> JsonList:
        return [pickler.flatten(member) for member in instance]

    @staticmethod
    def restore(jsonified_object: JsonList, unpickler: Unpickler) -> list:
        return [unpickler.restore(member) for member in jsonified_object]
