from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, TypeVar

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

from kelpickle.strategy.base_strategy import BaseStrategy, ReductionResult
from kelpickle.common import JsonList

ListReductionResultMemberType = TypeVar("ListReductionResultMemberType", bound=ReductionResult)


class ListStrategy(BaseStrategy[list, JsonList[ListReductionResultMemberType]]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'list'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [list]

    @staticmethod
    def reduce(instance: list, pickler: Pickler) -> JsonList[ListReductionResultMemberType]:
        return [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]

    @staticmethod
    def restore(reduced_object: JsonList[ListReductionResultMemberType], unpickler: Unpickler) -> list:
        return [unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(reduced_object)]
