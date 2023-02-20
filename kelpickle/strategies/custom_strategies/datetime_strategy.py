from __future__ import annotations
from datetime import datetime
from typing import TypedDict

from kelpickle.common import Jsonable
from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler


class DatetimeStrategyResult(TypedDict):
    value: str
    fold: int
    tzinfo: Jsonable


@register_strategy(name='datetime', supported_types=datetime, auto_generate_reduction_references=True, consider_subclasses=False)
class DatetimeStrategy(BaseStrategy):
    def reduce(self, instance: datetime, pickler: Pickler) -> DatetimeStrategyResult:
        return {
            'value': instance.isoformat(),
            'fold': instance.fold,
            'tzinfo': pickler.reduce(instance.tzinfo, relative_key='tzinfo')
        }

    def restore_base(self, reduced_instance: DatetimeStrategyResult, unpickler: Unpickler) -> datetime:
        restored_tzinfo = unpickler.restore(reduced_instance['tzinfo'], relative_key='tzinfo')
        restored_datetime = datetime.fromisoformat(reduced_instance['value'])

        return restored_datetime.replace(fold=reduced_instance['fold'], tzinfo=restored_tzinfo)
