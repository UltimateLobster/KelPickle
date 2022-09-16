from __future__ import annotations
from typing import TYPE_CHECKING, Any

from kelpickle.common import Json

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


def reduce_key(key: Any, pickler: Pickler, *, relative_key: str) -> str:
    reduced_key = pickler.reduce(key, relative_key=relative_key)
    assert isinstance(reduced_key, str), "Complex dict keys are not yet supported"
    # TODO: Add support for complex keys
    return reduced_key


def reduce_dict(instance: dict, pickler: Pickler) -> Json:
    return {
        # TODO: This is just temporary values for the dictionary relative keys. We would need to reconsider them
        #      in order to maintain readability and when reading the result manually as well as consistency between
        #      pickling and unpickling.
        reduce_key(key, pickler, relative_key=f"{i}_KEY"): pickler.reduce(value, relative_key=str(i))
        for i, (key, value) in enumerate(instance.items())
 }


def restore_dict(reduced_object: Json, unpickler: Unpickler) -> dict:
    result = {}
    for i, (key, value) in enumerate(reduced_object.items()):
        result[unpickler.restore(key, relative_key=f"{i}_KEY")] = unpickler.restore(value, relative_key=str(i))

    return result
