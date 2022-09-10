from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import tzinfo, datetime

from kelpickle.strategies.custom_strategy import ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

_some_datetime = datetime.now()


class TzInfoStrategyResult(ReductionResult):
    offset: Optional[float]
    tzinfo: ReductionResult


def reduce_tzinfo(instance: tzinfo, pickler: Pickler) -> TzInfoStrategyResult:
    offset_delta = instance.utcoffset(_some_datetime)
    offset_seconds = offset_delta.total_seconds() if offset_delta else None
    return {
        'tzinfo': pickler.default_reduce(instance),
        'offset': offset_seconds
    }


def restore_tzinfo(reduced_object: TzInfoStrategyResult, unpickler: Unpickler) -> tzinfo:
    restored_tzinfo = unpickler.default_restore(reduced_object['tzinfo'])
    assert isinstance(restored_tzinfo, tzinfo), f"Expected tzinfo upon unpickling. Received {type(restored_tzinfo)}"

    return restored_tzinfo
