from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

from kelpickle.common import JsonList


def reduce_list(instance: list, pickler: Pickler) -> JsonList:
    return [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]


def restore_list(reduced_object: JsonList, unpickler: Unpickler) -> list:
    return [unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(reduced_object)]
