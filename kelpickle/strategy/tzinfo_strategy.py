from __future__ import annotations
from typing import TYPE_CHECKING, Iterable
from datetime import tzinfo, datetime

from kelpickle.strategy.base_strategy import BaseNonNativeJsonStrategy, JsonicReductionResult, ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

_some_datetime = datetime.now()


class TzInfoStrategyResult(JsonicReductionResult):
    offset: float
    tzinfo: ReductionResult


class TzInfoStrategy(BaseNonNativeJsonStrategy[tzinfo, TzInfoStrategyResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'tzinfo'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [tzinfo]

    @staticmethod
    def reduce(instance: tzinfo, pickler: Pickler) -> TzInfoStrategyResult:
        return {
            'offset': instance.utcoffset(_some_datetime).total_seconds(),
            'tzinfo': pickler.default_reduce(instance)
        }

    @staticmethod
    def restore(reduced_object: TzInfoStrategyResult, unpickler: Unpickler) -> tzinfo:
        restored_tzinfo = unpickler.default_restore(reduced_object['tzinfo'])

        return restored_tzinfo
