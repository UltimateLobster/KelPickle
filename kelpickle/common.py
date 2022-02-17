from __future__ import annotations

from types import NoneType
from typing import TypeVar, TypeAlias, Any

# Obviously this is not the correct way to type these. Unfortunately the recursive nature of JSON prevents us to do it.
# This will hopefully be supported in the future which will let us change this correctly
JsonNative: TypeAlias = str | int | float | bool | NoneType
Json: TypeAlias = dict[str, Any]
JsonList: TypeAlias = list[Any]
Jsonable: TypeAlias = Json | JsonList | JsonNative

StateType = TypeVar('StateType')


NATIVE_TYPES = (int, float, bool, str, NoneType)

_T = TypeVar('_T')


def identity(x: _T) -> _T:
    return x


STRATEGY_KEY = 'py/strategy'
