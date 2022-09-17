from __future__ import annotations

from typing import TypedDict

from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy
from kelpickle.common import JsonList
from kelpickle.kelpickling import Pickler, Unpickler


class TupleReductionResult(TypedDict):
    value: JsonList


@register_strategy('tuple', supported_types=tuple)
class TupleStrategy(Strategy):
    @staticmethod
    def reduce(instance: tuple, pickler: Pickler) -> TupleReductionResult:
        return {'value': [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]}

    @staticmethod
    def restore(reduced_object: TupleReductionResult, unpickler: Unpickler) -> tuple:
        # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
        #  (Use PyTuple_SET)
        return tuple(unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(reduced_object['value']))
