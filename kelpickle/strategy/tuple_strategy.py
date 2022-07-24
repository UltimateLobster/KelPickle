from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from kelpickle.common import JsonList
from kelpickle.strategy.base_strategy import BaseNonNativeJsonStrategy, JsonicReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class TupleReductionResult(JsonicReductionResult):
    value: JsonList


class TupleStrategy(BaseNonNativeJsonStrategy[tuple, TupleReductionResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'tuple'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [tuple]

    @staticmethod
    def reduce(instance: tuple, pickler: Pickler) -> TupleReductionResult:
        return {'value': [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]}

    @staticmethod
    def restore(reduced_object: TupleReductionResult, unpickler: Unpickler) -> tuple:
        # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
        #  (Use PyTuple_SET)
        return tuple(unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(reduced_object['value']))
