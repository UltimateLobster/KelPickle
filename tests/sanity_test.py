from __future__ import annotations

import math
import pytest

from types import MethodType
from typing import Iterable, Any, Callable, Optional

from dataclasses import dataclass
from datetime import date, time, datetime, timedelta, timezone, tzinfo

from kelpickle.kelpickling import Pickler, Unpickler


def custom_function():
    pass


@dataclass
class CustomObject:
    x: int

    def custom_method(self):
        pass

    @staticmethod
    def custom_static_method():
        return 1

    @classmethod
    def custom_class_method(cls):
        return 1

    @property
    def custom_property(self):
        return 1


@dataclass(frozen=True)
class FrozenDataClass:
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


@dataclass
class CustomReduceExObject:
    supported_protocol: int

    def __reduce_ex__(self, protocol):
        if protocol != self.supported_protocol:
            raise Exception(f"Reduce ex was called with a protocol that is not supported by {CustomReduceExObject}")

        return CustomReduceExObject, (self.supported_protocol,), {}


class CustomSlottedClass:
    __slots__ = ("x",)

    def __init__(self, x: int):
        self.x = x

    def __eq__(self, other):
        return type(self) == type(other) and self.x == other.x


class CustomSlottedClassWithDynamicDict:
    __slots__ = ("x", "__dict__")

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return type(self) == type(other) and self.x == other.x and self.y == other.y


class CustomTzInfo(tzinfo):
    def __init__(self, offset: timedelta):
        self.offset = offset

    def __getinitargs__(self):
        return self.offset,

    def utcoffset(self, dt: datetime) -> timedelta:
        return self.offset

    def tzname(self, dt: datetime) -> str:
        return "CustomTzInfo"

    def dst(self, dt: datetime) -> timedelta:
        return timedelta(0)

    def __eq__(self, other):
        return type(self) == type(other) and self.offset == other.offset


def default_value_comparison(original_value, deserialized_value) -> bool:
    return type(original_value) == type(deserialized_value) and original_value == deserialized_value


def builtin_method_sanity_test(original_value, deserialized_value) -> bool:
    return default_value_comparison(original_value.__self__, deserialized_value.__self__)


def method_sanity_test(original_value: MethodType, deserialized_value: MethodType) -> bool:
    return original_value.__func__ == deserialized_value.__func__ and builtin_method_sanity_test(original_value, deserialized_value)


class SanityTestParams:
    def __init__(self,
                 test_name: str,
                 test_object: Any,
                 value_comparison: Optional[Callable[[Any, Any], bool]] = default_value_comparison
                 ):
        self.test_name = test_name
        self.test_object = test_object
        self.value_comparison = value_comparison


def create_sanity_test_params() -> Iterable[SanityTestParams]:
    return [
        SanityTestParams("NoneType", None),
        SanityTestParams("bool", True),
        SanityTestParams("integer", 1),
        SanityTestParams("float", 1.2),
        SanityTestParams("rounded float", 1.0),
        SanityTestParams("complex", 1 + 2j),
        SanityTestParams("infinite float", float('inf')),
        SanityTestParams("nan", float('nan'), lambda x, y: math.isnan(x) and math.isnan(y)),
        SanityTestParams("big integer", 1000000000000000000000),
        SanityTestParams("string", "some_string"),
        SanityTestParams("unicode string", 'עברית'),
        SanityTestParams("bytes", b'\x00\x01\x02'),
        SanityTestParams("list", [1, 2, 3]),
        SanityTestParams("tuple", (1, 2, 3)),
        SanityTestParams("set", {1, 2, 3}),
        SanityTestParams("dict", {'a': 2}),
        SanityTestParams("date", date(2020, 1, 1)),
        SanityTestParams("time", time(10, 0, 0, 0)),
        SanityTestParams("tz aware time", time(10, 0, 0, 0, tzinfo=CustomTzInfo(timedelta(hours=1)))),
        SanityTestParams("datetime", datetime(2020, 1, 1, 10, 0, 0, 0)),
        SanityTestParams("utc tzinfo", timezone.utc),
        SanityTestParams("custom tzinfo", CustomTzInfo(timedelta(hours=1))),
        SanityTestParams("tz aware datetime", datetime(2020, 1, 1, 10, 0, 0, 0, timezone.utc)),
        SanityTestParams("custom tzinfo datetime", datetime(2020, 1, 1, 10, 0, 0, 0, CustomTzInfo(timedelta(hours=1)))),
        SanityTestParams("custom object", CustomObject(1)),
        SanityTestParams("function", custom_function),
        SanityTestParams("method of simple instance", CustomObject(3).custom_method, method_sanity_test),
        SanityTestParams("method of simple class", CustomObject.custom_method),
        SanityTestParams("class method of simple instance", CustomObject(3).custom_class_method, method_sanity_test),
        SanityTestParams("class method of simple class", CustomObject.custom_class_method),
        SanityTestParams("static method of simple instance", CustomObject(3).custom_static_method),
        SanityTestParams("static method of simple class", CustomObject.custom_static_method),
        SanityTestParams("method wrapper", CustomObject(3).__str__, builtin_method_sanity_test),
        SanityTestParams("method wrapper descriptor", CustomObject.__str__),
        SanityTestParams("builtin function", sum),
        SanityTestParams("builtin method", [].append, builtin_method_sanity_test),
        SanityTestParams("builtin method descriptor", list.append),
        SanityTestParams("class method descriptor", dict.__dict__["fromkeys"], lambda x, y: pytest.skip(
            "Class method descriptors (Or at least the one used in the types module) are not equal even after the "
            "official pickling process.")),
        SanityTestParams("iterator", iter([1, 2, 3]), lambda x, y: list(x) == list(y)),
        SanityTestParams("not implemented", NotImplemented),
        SanityTestParams("module", CustomObject.__module__),
        SanityTestParams("class", CustomObject),
        SanityTestParams("simple instance", CustomObject(3)),
        SanityTestParams("frozen dataclass", FrozenDataClass(3)),
        SanityTestParams("instance with state", CustomStateObject(3)),
        SanityTestParams("instance with reduce", CustomReduceObject(3)),
        SanityTestParams("instance with reduce_ex", CustomReduceExObject(Pickler.PICKLE_PROTOCOL)),
        SanityTestParams("instance with slots", CustomSlottedClass(3)),
        SanityTestParams("instance with slots and dynamic dict", CustomSlottedClassWithDynamicDict(3, 4)),
        SanityTestParams("ellipsis", ...),
    ]


test_sanity_ids, test_sanity_objects, test_sanity_assertions = zip(*[
    (params.test_name, params.test_object, params.value_comparison)
    for params in create_sanity_test_params()]
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


@pytest.mark.parametrize(
    ['value'],
    [
        (CustomObject.custom_property,)
    ],
    ids=["property"]
)
def test_pickling_error_for_unpickleable_objects(value):
    pickler = Pickler()
    with pytest.raises(TypeError):
        pickler.pickle(value)
