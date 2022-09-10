from __future__ import annotations

from typing import TYPE_CHECKING

from kelpickle.common import JsonList
from kelpickle.strategies.custom_strategy import ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


class TupleReductionResult(ReductionResult):
    value: JsonList


def reduce_tuple(instance: tuple, pickler: Pickler) -> TupleReductionResult:
    return {'value': [pickler.reduce(member, relative_key=str(i)) for i, member in enumerate(instance)]}


def restore_tuple(reduced_object: TupleReductionResult, unpickler: Unpickler) -> tuple:
    # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
    #  (Use PyTuple_SET)
    return tuple(unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(reduced_object['value']))
