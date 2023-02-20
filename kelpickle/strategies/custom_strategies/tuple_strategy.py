from __future__ import annotations

from typing import TypedDict

from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.common import JsonList
from kelpickle.kelpickling import Pickler, Unpickler


class TupleReductionResult(TypedDict):
    value: JsonList


@register_strategy(name='tuple', supported_types=tuple, auto_generate_reduction_references=True, consider_subclasses=False)
class TupleStrategy(BaseStrategy):
    def reduce(self, instance: tuple, pickler: Pickler) -> TupleReductionResult:
        return {'value': [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]}

    def restore_base(self, reduced_instance: TupleReductionResult, unpickler: Unpickler) -> tuple:
        # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
        #  (Use PyTuple_SET)
        return tuple(unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(reduced_instance['value']))
