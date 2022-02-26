from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class SetStrategy(BaseStrategy[set]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'set'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [set]

    @staticmethod
    def simplify(instance: set, pickler: Pickler) -> Json:
        return {'value': [pickler.simplify(member) for member in instance]}

    @staticmethod
    def restore(simplified_object: Json, unpickler: Unpickler) -> set:
        return {unpickler.restore(member) for member in simplified_object['value']}
