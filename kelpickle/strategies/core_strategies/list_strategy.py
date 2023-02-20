from __future__ import annotations

from typing import TYPE_CHECKING

from kelpickle.strategies.base_strategy import BaseStrategy, register_core_strategy
if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

from kelpickle.common import JsonList


@register_core_strategy(
    auto_generate_reduction_references=True,
    supported_type=list
)
class ListStrategy(BaseStrategy):
    def reduce(self, *, instance: list, pickler: Pickler) -> JsonList:
        return [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]

    def restore_base(self, *, reduced_instance: JsonList, unpickler: Unpickler) -> list:
        return []

    def restore_rest(self, *, reduced_instance: list, unpickler: Unpickler, base_instance: list) -> None:
        for i, member in enumerate(reduced_instance):
            base_instance.append(unpickler.restore(member, relative_key=str(i)))
