from __future__ import annotations

import math
from datetime import date, time, datetime, timedelta, timezone

import pytest

from kelpickle.kelpickling import Pickler, Unpickler
import tests.objects_db
from tests.objects_db import DataClass, TestParameters, TzInfo, function, FrozenDataClass, CustomStateDataClass, \
    CustomReduceClass, CustomReduceExClass, SlottedClass, SlottedClassWithDynamicDict, Object


@pytest.mark.parametrize(['test_value'], [
    [TestParameters("integer", 1)],
    [TestParameters("float", 1.2)],
    [TestParameters("rounded float", 1.0)],
    [TestParameters("complex", 1 + 2j)],
    [TestParameters("infinite float", float('inf'))],
    [TestParameters("big integer", 1000000000000000000000)],
    [TestParameters("string", "some_string")],
    [TestParameters("non ascii string", 'There are א0 natural numbers.')],
    [TestParameters("bytes", b'\x00\x01\x02')],
    [TestParameters("list", [1, 2, 3])],
    [TestParameters("tuple", (1, 2, 3))],
    [TestParameters("set", {1, 2, 3})],
    [TestParameters("dict", {'a': 2})],
    [TestParameters("range", range(1))],
    [TestParameters("instance", DataClass(1))],
    [TestParameters("frozen instance", FrozenDataClass(3))],
    [TestParameters("instance with get/set state", CustomStateDataClass(3))],
    [TestParameters("instance with reduce", CustomReduceClass(3))],
    [TestParameters("instance with reduce_ex", CustomReduceExClass(Pickler.PICKLE_PROTOCOL, 1))],
    [TestParameters("instance with slots", SlottedClass(3))],
    [TestParameters("instance with slots and dynamic dict", SlottedClassWithDynamicDict(3, 4))],
    [TestParameters("classmethod", Object.custom_class_method)],
    [TestParameters("static method instance descriptor", Object(3).custom_static_method)],
    ],
    ids=lambda x: x.description
)
def test_equal_values(test_value: TestParameters):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(test_value.value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert test_value.value == deserialized_value


@pytest.mark.parametrize(['test_value'], [
        [TestParameters("NoneType", None)],
        [TestParameters("not implemented", NotImplemented)],
        [TestParameters("ellipsis", ...)],
        [TestParameters("bool", True)],
        [TestParameters("builtin function", sum)],
        [TestParameters("builtin class", list)],
        [TestParameters("function", function)],
        [TestParameters("class", DataClass)],
        [TestParameters("method of simple class", Object.custom_method)],
        [TestParameters("static method", Object.custom_static_method)],
        [TestParameters("method wrapper descriptor", Object.__str__)],
        [TestParameters("builtin method descriptor", list.append)],
    ],
    ids=lambda x: x.description
)
def test_identity_values(test_value: TestParameters):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(test_value.value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert test_value.value is deserialized_value


@pytest.mark.parametrize(['test_value'], [
        [TestParameters("method descriptor", Object(3).custom_method)],
    ],
    ids=lambda x: x.description
)
def test_instance_method_descriptors_retain_owner(test_value: TestParameters):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(test_value.value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert type(test_value.value) == type(deserialized_value)
    assert test_value.value.__func__ == deserialized_value.__func__

    original_owner = test_value.value.__self__
    deserialized_owner = deserialized_value.__self__
    assert type(original_owner) is type(deserialized_owner) is Object
    assert original_owner.x == deserialized_owner.x


@pytest.mark.parametrize(['test_value'], [
    [TestParameters("class method descriptor", Object(3).custom_class_method)],
    [TestParameters("builtin method wrapper", [].__str__)],
    [TestParameters("builtin method", [].append)],
    ],
    ids=lambda x: x.description
)
def test_descriptors_retain_owner(test_value: TestParameters):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(test_value.value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert type(test_value.value) is type(deserialized_value)
    assert test_value.value.__self__ == deserialized_value.__self__


@pytest.mark.parametrize(['test_value'], [
    [TestParameters("class method descriptor", Object(3).custom_class_method)],
    ],
    ids=lambda x: x.description
)
def test_method_descriptors_retain_wrapped_function(test_value: TestParameters):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(test_value.value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert type(test_value.value) is type(deserialized_value)
    assert test_value.value.__func__ == deserialized_value.__func__


def test_iterator():
    pickler = Pickler()
    unpickler = Unpickler()
    iterator = iter([1, 2, 3])
    serialized_value = pickler.pickle(iterator)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert list(iterator) == list(deserialized_value)


def test_nan():
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(float('nan'))
    deserialized_value = unpickler.unpickle(serialized_value)

    assert type(deserialized_value) is float
    assert math.isnan(deserialized_value)


@pytest.mark.parametrize(
    ['test_value'],
    [
        [TestParameters("property", Object.custom_property)],
        [TestParameters("module", tests.objects_db)],
        [TestParameters("builtin module", math)],
    ],
    ids=lambda x: x.description
)
def test_pickling_error_for_unpickleable_objects(test_value):
    pickler = Pickler()
    with pytest.raises(TypeError):
        pickler.pickle(test_value.value)


@pytest.mark.parametrize(['test_value'], [
        [TestParameters("date", date(2020, 1, 1))],
        [TestParameters("time", time(10))],
        [TestParameters("datetime", datetime(2020, 1, 1, 10))],
        [TestParameters("tzinfo", timezone.utc)],
        [TestParameters("tz aware time", time(10, tzinfo=timezone.utc))],
        [TestParameters("tz aware datetime", datetime(2020, 1, 1, 10, 0, 0, 0, timezone.utc))],
        [TestParameters("custom tzinfo", TzInfo(timedelta(hours=1)))],
        [TestParameters("custom tz aware time", time(10, tzinfo=TzInfo(timedelta(hours=1))))],
        [TestParameters("custom tz aware datetime", datetime(2020, 1, 1, 10, tzinfo=TzInfo(timedelta(hours=1))))],
    ],
    ids=lambda x: x.description
)
def test_datetime_values(test_value: TestParameters):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(test_value.value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assert test_value.value == deserialized_value
