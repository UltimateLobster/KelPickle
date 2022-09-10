from __future__ import annotations
import base64
from typing import TYPE_CHECKING

from kelpickle.strategies.custom_strategy import ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class BytesReductionResult(ReductionResult):
    buffer: str


def reduce_bytes(instance: bytes, pickler: Pickler) -> BytesReductionResult:
    return {'buffer': base64.b64encode(instance).decode('utf-8')}


def restore_bytes(reduced_object: BytesReductionResult, unpickler: Unpickler) -> bytes:
    return base64.b64decode(reduced_object['buffer'])
