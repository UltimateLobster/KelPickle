from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar
from kelpickle.common import JsonNative

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


NativeT = TypeVar("NativeT", bound=JsonNative)


def reduce_native(instance: NativeT, pickler: Pickler) -> NativeT:
    return instance


def restore_native(reduced_object: NativeT, unpickler: Unpickler) -> NativeT:
    return reduced_object
