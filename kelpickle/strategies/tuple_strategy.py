from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class TupleStrategy(BaseStrategy[tuple]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'tuple'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [tuple]

    @staticmethod
    def simplify(instance: tuple, pickler: Pickler) -> Json:
        return {'value': [pickler.simplify(member) for member in instance]}

    @staticmethod
    def restore(simplified_object: Json, unpickler: Unpickler) -> tuple:
        # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
        #  (Use PyTuple_SET)
        return tuple(unpickler.restore(member) for member in simplified_object['value'])
