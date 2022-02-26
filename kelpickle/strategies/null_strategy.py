from __future__ import annotations

from typing import TYPE_CHECKING, Iterable
from kelpickle.common import JsonNative, NATIVE_TYPES
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class NullStrategy(BaseStrategy[JsonNative]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'null'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return NATIVE_TYPES

    @staticmethod
    def simplify(instance: JsonNative, pickler: Pickler) -> JsonNative:
        return instance

    @staticmethod
    def restore(simplified_object: JsonNative, unpickler: Unpickler) -> JsonNative:
        return simplified_object
