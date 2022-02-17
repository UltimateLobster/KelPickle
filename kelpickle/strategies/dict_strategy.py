from __future__ import annotations

from typing import TYPE_CHECKING

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import JsonStrategy

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


class DictStrategy(JsonStrategy[dict]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'dict'

    @staticmethod
    def _flatten(instance: dict, pickler: Pickler) -> Json:
        return {
            pickler.flatten(key): pickler.flatten(value)
            for key, value in instance.items()
        }

    @staticmethod
    def restore(jsonified_object: Json, unpickler: Unpickler) -> dict:
        result = {}
        for key, value in jsonified_object.items():
            result[unpickler.restore(key)] = unpickler.restore(value)

        return result
