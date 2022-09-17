from __future__ import annotations
import base64
from typing import TypedDict

from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy

from kelpickle.kelpickling import Pickler, Unpickler


class BytesReductionResult(TypedDict):
    buffer: str


@register_strategy('bytes', supported_types=bytes)
class BytesStrategy(Strategy):
    @staticmethod
    def reduce(instance: bytes, pickler: Pickler) -> BytesReductionResult:
        return {'buffer': base64.b64encode(instance).decode('utf-8')}

    @staticmethod
    def restore(reduced_object: BytesReductionResult, unpickler: Unpickler) -> bytes:
        return base64.b64decode(reduced_object['buffer'])
