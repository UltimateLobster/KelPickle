from __future__ import annotations
import pytest
from dataclasses import dataclass

from kelpickle.pickler import Pickler
from kelpickle.unpickler import Unpickler


@dataclass
class CustomObject:
    x: int


class CustomStateObject(CustomObject):
    def __init__(self, x: int):
        super().__init__(x)
        self.y = x

    def __getstate__(self):
        return {"x": self.x}

    def __setstate__(self, state):
        self.x = state["x"]
        self.y = state["x"]


class CustomReduceObject(CustomObject):
    def __reduce__(self):
        return CustomReduceObject, (self.x,), {}


def custom_function():
    pass


@pytest.mark.parametrize(
    'value',
    [
        None,
        True,
        1,
        1.2,
        1.0,
        1000000000000000000000,
        'some_string',
        'עברית',
        [1, 2, 3],
        (1, 2, 3),
        {1, 2, 3},
        {'a': 2},
        CustomObject.__module__,
        CustomObject,
        custom_function,
        CustomObject(3),
        CustomStateObject(3),
        CustomReduceObject(3),
        ...
    ]
)
def test_sanity(value):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert deserialized_value == value
