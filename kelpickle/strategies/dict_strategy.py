from __future__ import annotations

from typing import TYPE_CHECKING
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


class DictStrategy(BaseStrategy):
    @staticmethod
    def get_strategy_name() -> str:
        return 'dict'

    @staticmethod
    def populate_json(instance: dict, jsonified_instance: dict[str], pickler: Pickler) -> None:
        for key, value in instance.items():
            jsonified_instance[pickler.flatten(key)] = pickler.flatten(value)

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> dict:
        result = {}
        for key, value in jsonified_object.items():
            result[unpickler.restore(key)] = unpickler.restore(value)

        return result
