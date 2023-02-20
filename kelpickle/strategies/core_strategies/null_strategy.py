from __future__ import annotations

from types import NoneType
from typing import TYPE_CHECKING, TypeVar

from kelpickle.strategies.base_strategy import BaseStrategy, register_core_strategy
from kelpickle.common import JsonNative

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


NativeT = TypeVar("NativeT", bound=JsonNative)


@register_core_strategy(auto_generate_reduction_references=False, supported_type=str)
@register_core_strategy(auto_generate_reduction_references=False, supported_type=int)
@register_core_strategy(auto_generate_reduction_references=False, supported_type=float)
@register_core_strategy(auto_generate_reduction_references=False, supported_type=bool)
@register_core_strategy(auto_generate_reduction_references=False, supported_type=NoneType)
class EmptyStrategy(BaseStrategy):
    def reduce(self, *, instance: NativeT, pickler: Pickler) -> NativeT:
        return instance

    def restore_base(self, *, reduced_instance: NativeT, unpickler: Unpickler) -> NativeT:
        return reduced_instance

