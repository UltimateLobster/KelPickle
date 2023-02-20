from __future__ import annotations

from dataclasses import dataclass
from datetime import tzinfo, timedelta, datetime
from typing import Any, TypeVar

from kelpickle.kelpickling import Pickler

T = TypeVar('T')


@dataclass
class TestParameters:
    __test__ = False

    description: str
    value: Any
    

def function():
    pass


class Object:
    def __init__(self, x: Any):
        self.x = x

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


@dataclass
class DataClass:
    x: Any


@dataclass(frozen=True)
class FrozenDataClass:
    x: Any


class CustomStateDataClass(DataClass):
    def __init__(self, x: Any):
        super().__init__(x)
        self.y = x

    def __getstate__(self):
        return {"x": self.x}

    def __setstate__(self, state):
        self.x = state["x"]
        self.y = state["x"]


class CustomReduceClass(DataClass):
    def __reduce__(self):
        return CustomReduceClass, (self.x,), {}


@dataclass
class CustomReduceExClass:
    supported_protocol: int
    x: Any

    def __reduce_ex__(self, protocol):
        if protocol != self.supported_protocol:
            raise Exception(f"Reduce ex was called with a protocol that is not supported by {CustomReduceExClass}")

        return CustomReduceExClass, (self.supported_protocol, self.x), {}


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
