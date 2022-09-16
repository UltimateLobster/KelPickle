from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, TypedDict

from kelpickle.common import Jsonable
from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class DatetimeStrategyResult(TypedDict):
    value: str
    fold: int
    tzinfo: Jsonable


@register_strategy('datetime', supported_types=datetime)
class DatetimeStrategy(Strategy):
    @staticmethod
    def reduce(instance: datetime, pickler: Pickler) -> DatetimeStrategyResult:
        return {
            'value': instance.isoformat(),
            'fold': instance.fold,
            'tzinfo': pickler.reduce(instance.tzinfo, relative_key='tzinfo')
        }

    @staticmethod
    def restore(reduced_object: DatetimeStrategyResult, unpickler: Unpickler) -> datetime:
        restored_tzinfo = unpickler.restore(reduced_object['tzinfo'], relative_key='tzinfo')
        restored_datetime = datetime.fromisoformat(reduced_object['value'])

        return restored_datetime.replace(fold=reduced_object['fold'], tzinfo=restored_tzinfo)
