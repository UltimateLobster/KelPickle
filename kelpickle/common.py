from __future__ import annotations

from types import NoneType
from typing import Optional, TypeAlias, Any, Callable, Iterable, TypeVar

# Represents the generic instance one would want to pickle
InstanceType = TypeVar('InstanceType')
InstanceState: TypeAlias = dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]
ReduceResult: TypeAlias = str | tuple[
    Callable,
    Iterable,
    Optional[InstanceState | Any],
    Optional[Iterable],
    Optional[Iterable[tuple[str, Any]]],
    Optional[Callable[[Any, InstanceState], None]]
]

NATIVE_TYPES = (int, float, bool, str, NoneType)

_T = TypeVar('_T')


def null_function(x: _T) -> _T:
    return x
