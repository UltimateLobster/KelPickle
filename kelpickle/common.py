from __future__ import annotations

from types import NoneType
from typing import Optional, TypeAlias, Any, Callable, Iterable, TypeVar

# Represents the generic instance one would want to pickle
InstanceType = TypeVar('InstanceType')

NATIVE_TYPES = (int, float, bool, str, NoneType)

_T = TypeVar('_T')


def identity(x: _T) -> _T:
    return x


STRATEGY_KEY = 'py/strategy'
