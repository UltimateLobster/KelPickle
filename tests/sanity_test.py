from __future__ import annotations
import pytest

from kelpickle.pickler import Pickler
from kelpickle.unpickler import Unpickler


class CustomObject:
    def __init__(self, x: int):
        self.x = x

    def __eq__(self, other: CustomObject):
        return self.__class__ == other.__class__ and self.x == other.x


@pytest.mark.parametrize(
    'value',
    [
        [None],
        [True],
        [1],
        [1.2],
        [1.0],
        [1000000000000000000000],
        ['some_string'],
        ['עברית'],
        [[1, 2, 3]],
        [{'a': 2}],
        [CustomObject(3)]
    ]
)
def test_sanity(value):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert deserialized_value == value
