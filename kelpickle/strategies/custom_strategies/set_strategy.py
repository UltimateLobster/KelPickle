from __future__ import annotations

from typing import TypedDict

from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.common import JsonList
from kelpickle.kelpickling import Pickler, Unpickler


class SetReductionResult(TypedDict):
    value: JsonList


@register_strategy(name='set', supported_types=set, auto_generate_reduction_references=True, consider_subclasses=False)
class SetStrategy(BaseStrategy):
    def reduce(self, instance: set, pickler: Pickler) -> SetReductionResult:
        # We allow ourselves to have the relative key work by index even though this is a set (which is supposedly
        # unordered) this is fine because we are basically converting it to an order list and it will stay as an order
        # list for all the steps that use the relative key.
        return {'value': [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]}

    def restore_base(self, reduced_instance: SetReductionResult, unpickler: Unpickler) -> set:
        return set()

    def restore_rest(self, *, reduced_instance: SetReductionResult, unpickler: Unpickler, base_instance: set):
        for i, member in enumerate(reduced_instance["value"]):
            base_instance.add(unpickler.restore(member, relative_key=str(i)))
