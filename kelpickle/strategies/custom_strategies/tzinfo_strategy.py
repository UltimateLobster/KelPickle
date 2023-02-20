from __future__ import annotations
from typing import Optional, TypedDict
from datetime import tzinfo, datetime

from kelpickle.common import Jsonable
from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler

_some_datetime = datetime.now()


class TzInfoStrategyResult(TypedDict):
    offset: Optional[float]
    tzinfo: Jsonable


@register_strategy(name='tzinfo', supported_types=tzinfo, auto_generate_reduction_references=True, consider_subclasses=True)
class TzInfoStrategy(BaseStrategy):
    def reduce(self, instance: tzinfo, pickler: Pickler) -> TzInfoStrategyResult:
        offset_delta = instance.utcoffset(_some_datetime)
        offset_seconds = offset_delta.total_seconds() if offset_delta else None
        return {
            'tzinfo': pickler.default_reduce(instance),
            'offset': offset_seconds
        }

    def restore_base(self, reduced_instance: TzInfoStrategyResult, unpickler: Unpickler) -> tzinfo:
        restored_tzinfo = unpickler.default_restore(reduced_instance['tzinfo'])
        assert isinstance(restored_tzinfo, tzinfo), f"Expected tzinfo upon unpickling. Received {type(restored_tzinfo)}"

        return restored_tzinfo
