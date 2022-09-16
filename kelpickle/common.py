from __future__ import annotations

from types import NoneType
from typing import TypeAlias, Any, Literal

# Obviously this is not the correct way to type these. Unfortunately the recursive nature of JSON prevents us to do it.
# This will hopefully be supported in the future which will let us change this correctly
JsonNative: TypeAlias = int | float | bool | str | NoneType
JsonList: TypeAlias = list[Any]
Json: TypeAlias = dict[str, Any]

Jsonable: TypeAlias = Json | JsonList | JsonNative


NATIVE_TYPES = (int, float, bool, str, NoneType)
KELP_STRATEGY_KEY: Literal["kelp/strategy"] = 'kelp/strategy'


class PicklingError(Exception):
    """
    Error that occurs during the pickling process
    """
    pass
