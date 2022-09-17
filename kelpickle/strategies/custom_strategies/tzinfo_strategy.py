from __future__ import annotations
from typing import Optional, TypedDict
from datetime import tzinfo, datetime

from kelpickle.common import Jsonable
from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler

_some_datetime = datetime.now()


class TzInfoStrategyResult(TypedDict):
    offset: Optional[float]
    tzinfo: Jsonable


@register_strategy('tzinfo', supported_types=tzinfo, consider_subclasses=True)
class TzInfoStrategy(Strategy):
    @staticmethod
    def reduce(instance: tzinfo, pickler: Pickler) -> TzInfoStrategyResult:
        offset_delta = instance.utcoffset(_some_datetime)
        offset_seconds = offset_delta.total_seconds() if offset_delta else None
        return {
            'tzinfo': pickler.default_reduce(instance),
            'offset': offset_seconds
        }

    @staticmethod
    def restore(reduced_object: TzInfoStrategyResult, unpickler: Unpickler) -> tzinfo:
        restored_tzinfo = unpickler.default_restore(reduced_object['tzinfo'])
        assert isinstance(restored_tzinfo, tzinfo), f"Expected tzinfo upon unpickling. Received {type(restored_tzinfo)}"

        return restored_tzinfo
