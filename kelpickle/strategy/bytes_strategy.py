from __future__ import annotations
import base64
from typing import TYPE_CHECKING, Iterable, TypedDict

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

from kelpickle.strategy.base_strategy import BaseNonNativeJsonStrategy, JsonicReductionResult


class BytesReductionResult(JsonicReductionResult):
    buffer: str


class BytesStrategy(BaseNonNativeJsonStrategy[bytes, BytesReductionResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'base64'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [bytes]

    @staticmethod
    def reduce(instance: bytes, pickler: Pickler) -> BytesReductionResult:
        return {'buffer': base64.b64encode(instance).decode('utf-8')}

    @staticmethod
    def restore(reduced_object: BytesReductionResult, unpickler: Unpickler) -> bytes:
        return base64.b64decode(reduced_object['buffer'])
