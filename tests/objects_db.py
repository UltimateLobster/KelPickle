from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import tzinfo, timedelta, datetime, date, time, timezone
from typing import Any, Callable, TypeVar

from kelpickle.kelpickling import Pickler

T = TypeVar('T')


def default_equality_function(original_value, deserialized_value) -> bool:
    return type(original_value) == type(deserialized_value) and original_value == deserialized_value


def builtin_method_equality(original_value, deserialized_value) -> bool:
    return type(original_value) == type(deserialized_value) and \
           default_equality_function(original_value.__self__, deserialized_value.__self__)


def method_equality(original_value, deserialized_value) -> bool:
    return builtin_method_equality(original_value, deserialized_value) \
            and original_value.__func__ == deserialized_value.__func__


@dataclass
class ObjectDetail:
    description: str
    value: Any
    equality_function: Callable[[Any, Any], bool] = default_equality_function
    

def function():
    pass


@dataclass
class Object:
    x: Any

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

    def __hash__(self):
        return object.__hash__(self)


@dataclass(frozen=True)
class FrozenDataClass:
    x: Any


class CustomStateObject(Object):
    def __init__(self, x: Any):
        super().__init__(x)
        self.y = x

    def __getstate__(self):
        return {"x": self.x}

    def __setstate__(self, state):
        self.x = state["x"]
        self.y = state["x"]


class CustomReduceObject(Object):
    def __reduce__(self):
        return CustomReduceObject, (self.x,), {}


@dataclass
class CustomReduceExObject:
    supported_protocol: int
    x: Any

    def __reduce_ex__(self, protocol):
        if protocol != self.supported_protocol:
            raise Exception(f"Reduce ex was called with a protocol that is not supported by {CustomReduceExObject}")

        return CustomReduceExObject, (self.supported_protocol, self.x), {}


class SlottedClass:
    __slots__ = ("x",)

    def __init__(self, x: Any):
        self.x = x

    def __eq__(self, other):
        return type(self) == type(other) and self.x == other.x


class SlottedClassWithDynamicDict:
    __slots__ = ("x", "__dict__")

    def __init__(self, x: Any, y: Any):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return type(self) == type(other) and self.x == other.x and self.y == other.y


class TzInfo(tzinfo):
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



circular_list = []
circular_list.append(circular_list)

circular_tuple = (Object(1),)
circular_tuple[0].x = circular_tuple

circular_set = set()
circular_set_container = Object(circular_set)
circular_set.add(circular_set_container)

circular_dict = {}
circular_dict["myself"] = circular_dict

circular_object = Object(1)
circular_object.x = circular_object

circular_frozen_dataclass = FrozenDataClass(1)
circular_frozen_dataclass.__dict__["x"] = circular_frozen_dataclass

circular_custom_state_object = CustomStateObject(1)
circular_custom_state_object.x = circular_custom_state_object
circular_custom_state_object.y = circular_custom_state_object

circular_custom_reduce_object = CustomReduceObject(1)
circular_custom_reduce_object.x = circular_custom_reduce_object

circular_custom_reduce_ex_object = CustomReduceExObject(Pickler.PICKLE_PROTOCOL, 1)
circular_custom_reduce_ex_object.x = circular_custom_reduce_ex_object

circular_slotted_object = SlottedClass(1)
circular_slotted_object.x = circular_slotted_object

circular_slotted_object_with_dynamic_dict = SlottedClassWithDynamicDict(1, 2)
circular_slotted_object_with_dynamic_dict.x = circular_slotted_object_with_dynamic_dict
circular_slotted_object_with_dynamic_dict.y = circular_slotted_object_with_dynamic_dict


all_objects: list[ObjectDetail] = [
    ObjectDetail("NoneType", None),
    ObjectDetail("bool", True),
    ObjectDetail("integer", 1),
    ObjectDetail("float", 1.2),
    ObjectDetail("rounded float", 1.0),
    ObjectDetail("complex", 1 + 2j),
    ObjectDetail("infinite float", float('inf')),
    ObjectDetail("nan", float('nan'), lambda x, y: math.isnan(x) and math.isnan(y)),
    ObjectDetail("big integer", 1000000000000000000000),
    ObjectDetail("string", "some_string"),
    ObjectDetail("unicode string", 'עברית'),
    ObjectDetail("bytes", b'\x00\x01\x02'),
    ObjectDetail("list", [1, 2, 3]),
    ObjectDetail("tuple", (1, 2, 3)),
    ObjectDetail("set", {1, 2, 3}),
    ObjectDetail("dict", {'a': 2}),
    ObjectDetail("date", date(2020, 1, 1)),
    ObjectDetail("time", time(10)),
    ObjectDetail("tz aware time", time(10, tzinfo=TzInfo(timedelta(hours=1)))),
    ObjectDetail("datetime", datetime(2020, 1, 1, 10)),
    ObjectDetail("utc tzinfo", timezone.utc),
    ObjectDetail("custom_strategies tzinfo", TzInfo(timedelta(hours=1))),
    ObjectDetail("tz aware datetime", datetime(2020, 1, 1, 10, 0, 0, 0, timezone.utc)),
    ObjectDetail("custom_strategies tzinfo datetime", datetime(2020, 1, 1, 10,
                                                               tzinfo=TzInfo(timedelta(hours=1)))),
    ObjectDetail("custom_strategies object", Object(1)),
    ObjectDetail("function", function),
    ObjectDetail("method of simple instance", Object(3).custom_method, method_equality),
    ObjectDetail("method of simple class", Object.custom_method),
    ObjectDetail("class method of simple instance", Object(3).custom_class_method, method_equality),
    ObjectDetail("class method of simple class", Object.custom_class_method),
    ObjectDetail("static method of simple instance", Object(3).custom_static_method),
    ObjectDetail("static method of simple class", Object.custom_static_method),
    ObjectDetail("method wrapper", Object(3).__str__, builtin_method_equality),
    ObjectDetail("method wrapper descriptor", Object.__str__),
    ObjectDetail("builtin function", sum),
    ObjectDetail("builtin method", [].append, builtin_method_equality),
    ObjectDetail("builtin method descriptor", list.append),
    ObjectDetail("iterator", iter([1, 2, 3]), lambda x, y: list(x) == list(y)),
    ObjectDetail("not implemented", NotImplemented),
    ObjectDetail("module", Object.__module__),
    ObjectDetail("class", Object),
    ObjectDetail("simple instance", Object(3)),
    ObjectDetail("frozen dataclass", FrozenDataClass(3)),
    ObjectDetail("instance with state", CustomStateObject(3)),
    ObjectDetail("instance with reduce", CustomReduceObject(3)),
    ObjectDetail("instance with reduce_ex", CustomReduceExObject(Pickler.PICKLE_PROTOCOL, 1)),
    ObjectDetail("instance with slots", SlottedClass(3)),
    ObjectDetail("instance with slots and dynamic dict", SlottedClassWithDynamicDict(3, 4)),
    ObjectDetail("ellipsis", ...),

    # Circular references
    ObjectDetail("circular list", circular_list, lambda x, y: type(x) is type(y) is list and x[0] is x and y[0] is y),
    ObjectDetail("circular tuple", circular_tuple),
    ObjectDetail("circular set", circular_set),
    ObjectDetail("circular dict", circular_dict),
    ObjectDetail("circular object", circular_object),
    ObjectDetail("circular frozen dataclass", circular_frozen_dataclass),
    ObjectDetail("circular instance with state", circular_custom_state_object),
    ObjectDetail("circular instance with reduce", circular_custom_reduce_object),
    ObjectDetail("circular instance with reduce_ex", circular_custom_reduce_ex_object),
    ObjectDetail("circular instance with slots", circular_slotted_object),
    ObjectDetail("circular instance with slots and dynamic dict", circular_slotted_object_with_dynamic_dict),
]
