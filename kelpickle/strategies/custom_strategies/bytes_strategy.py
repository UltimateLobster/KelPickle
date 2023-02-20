from __future__ import annotations
import base64
from typing import TypedDict

from kelpickle.kelpickling import Pickler, Unpickler
from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy


class BytesReductionResult(TypedDict):
    buffer: str


@register_strategy(name='bytes', supported_types=bytes, auto_generate_reduction_references=True, consider_subclasses=False)
class BytesStrategy(BaseStrategy):
    def reduce(self, instance: bytes, pickler: Pickler) -> BytesReductionResult:
        return {'buffer': base64.b64encode(instance).decode('utf-8')}

    def restore_base(self, *, reduced_instance: BytesReductionResult, unpickler: Unpickler) -> bytes:
        return base64.b64decode(reduced_instance['buffer'])
