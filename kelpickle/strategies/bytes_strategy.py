from __future__ import annotations
import base64
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import BaseStrategy


class BytesStrategy(BaseStrategy[bytes]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'base64'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [bytes]

    @staticmethod
    def simplify(instance: bytes, pickler: Pickler) -> Json:
        return {'buffer': base64.b64encode(instance).decode('utf-8')}

    @staticmethod
    def restore(simplified_object: Json, unpickler: Unpickler) -> bytes:
        return base64.b64decode(simplified_object['buffer'])
