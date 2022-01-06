from __future__ import annotations

from typing import TYPE_CHECKING
from kelpickle.strategies.base_strategy import BaseStrategy, T


if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


class TupleStrategy(BaseStrategy):
    @staticmethod
    def get_strategy_name() -> str:
        return 'tuple'

    @staticmethod
    def populate_json(instance: tuple, jsonified_instance: dict[str], pickler: Pickler) -> None:
        jsonified_instance['value'] = [pickler.flatten(member) for member in instance]

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> tuple:
        # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
        #  (Use PyTuple_SET)
        return tuple(unpickler.restore(member) for member in jsonified_object['value'])
