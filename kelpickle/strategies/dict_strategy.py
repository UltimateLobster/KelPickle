from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class DictStrategy(BaseStrategy[dict]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'dict'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [dict]

    @staticmethod
    def simplify(instance: dict, pickler: Pickler) -> Json:
        return {
            pickler.simplify(key): pickler.simplify(value)
            for key, value in instance.items()
        }

    @staticmethod
    def restore(simplified_object: Json, unpickler: Unpickler) -> dict:
        result = {}
        for key, value in simplified_object.items():
            result[unpickler.restore(key)] = unpickler.restore(value)

        return result
