from __future__ import annotations

import pytest

from kelpickle.kelpickling import Pickler, Unpickler
from tests.objects_db import all_objects, Object

test_sanity_ids, test_sanity_objects, test_sanity_assertions = zip(*[
    (object_detail.description, object_detail.value, object_detail.equality_function)
    for object_detail in all_objects]
)


@pytest.mark.parametrize(
    ['value', 'value_comparison'],
    zip(test_sanity_objects, test_sanity_assertions),
    ids=test_sanity_ids
)
def test_sanity(value, value_comparison):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert value_comparison(value, deserialized_value)


def test_reference_caching():
    pickler = Pickler()
    unpickler = Unpickler()

    value = []
    value_appears_twice = {
        'value': value,
        'value_again': value
    }

    serialized = pickler.pickle(value_appears_twice)
    deserialized = unpickler.unpickle(serialized)

    assert deserialized['value'] is deserialized['value_again']


@pytest.mark.parametrize(
    ['value'],
    [
        (Object.custom_property,)
    ],
    ids=["property"]
)
def test_pickling_error_for_unpickleable_objects(value):
    pickler = Pickler()
    with pytest.raises(TypeError):
        pickler.pickle(value)


@pytest.mark.skip("Test is not implemented yet")
def test_reduction_reference_collision():
    pass
