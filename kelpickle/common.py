from __future__ import annotations

from dataclasses import dataclass
from types import NoneType
from typing import TypeAlias, Any

# Obviously this is not the correct way to type these. Unfortunately the recursive nature of JSON prevents us to do it.
# This will hopefully be supported in the future which will let us change this correctly
JsonNative: TypeAlias = int | float | bool | str | NoneType
JsonList: TypeAlias = list[Any]
Json: TypeAlias = dict[str, Any]

Jsonable: TypeAlias = Json | JsonList | JsonNative

SAVED_WORDS_PREFIX = f"kelp/"
STRATEGY_KEY: str = f'{SAVED_WORDS_PREFIX}strategy'


@dataclass(frozen=True, slots=True)
class Unrestorable:
    reduced_object: Jsonable
    reason: str
