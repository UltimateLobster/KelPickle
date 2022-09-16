from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy
from kelpickle.common import JsonList

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class SetReductionResult(TypedDict):
    value: JsonList


@register_strategy('set', supported_types=set)
class SetStrategy(Strategy):
    @staticmethod
    def reduce(instance: set, pickler: Pickler) -> SetReductionResult:
        # We allow ourselves to have the relative key work by index even though this is a set (which is supposedly
        # unordered) this is fine because we are basically converting it to an order list and it will stay as an order
        # list for all the steps that use the relative key.
        return {'value': [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]}

    @staticmethod
    def restore(reduced_object: SetReductionResult, unpickler: Unpickler) -> set:
        return {unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(reduced_object['value'])}
