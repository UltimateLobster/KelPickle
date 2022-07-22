from __future__ import annotations

import pytest

from typing import Iterable, Any, Callable, Optional
from dataclasses import dataclass

from kelpickle.kelpickling import Pickler, Unpickler


@dataclass
class CustomObject:
    x: int

    def custom_method(self):
        pass


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


def custom_function():
    pass


def default_sanity_test(serialized, deserialized) -> bool:
    return type(serialized) == type(deserialized) and serialized == deserialized


class SanityTestParams:
    def __init__(self,
                 test_name: str,
                 test_object: Any,
                 should_pass_test: Optional[Callable[[Any, Any], bool]] = default_sanity_test
                 ):
        self.test_name = test_name
        self.test_object = test_object
        self.should_pass_test = should_pass_test


def create_sanity_test_params() -> Iterable[SanityTestParams]:
    return [
        SanityTestParams("NoneType", None),
        SanityTestParams("bool", True),
        SanityTestParams("integer", 1),
        SanityTestParams("float", 1.2),
        SanityTestParams("rounded float", 1.0),
        SanityTestParams("complex", 1 + 2j),
        SanityTestParams("infinite float", float('inf')),
        SanityTestParams("nan", float('nan')),
        SanityTestParams("big integer", 1000000000000000000000),
        SanityTestParams("string", "some_string"),
        SanityTestParams("unicode string", 'עברית'),
        SanityTestParams("bytes", b'\x00\x01\x02'),
        SanityTestParams("list", [1, 2, 3]),
        SanityTestParams("tuple", (1, 2, 3)),
        SanityTestParams("set", {1, 2, 3}),
        SanityTestParams("dict", {'a': 2}),
        SanityTestParams("function", custom_function),
        SanityTestParams("builtin function", sum),
        SanityTestParams("iterator", iter([])),
        SanityTestParams("wrapper descriptor", object.__init__),
        SanityTestParams("method wrapper", object().__str__),
        SanityTestParams("builtin method", [].append),
        SanityTestParams("class method descriptor", dict.__dict__["fromkeys"]),
        SanityTestParams("not implemented", NotImplemented),
        SanityTestParams("module", CustomObject.__module__),
        SanityTestParams("class", CustomObject),
        SanityTestParams("method of simple class", CustomObject.custom_method),
        SanityTestParams("simple instance", CustomObject(3)),
        SanityTestParams("method of simple instance", CustomObject(3).custom_method),
        SanityTestParams("frozen dataclass", FrozenDataClass(3)),
        SanityTestParams("instance with state", CustomStateObject(3)),
        SanityTestParams("instance with reduce", CustomReduceObject(3)),
        SanityTestParams("instance with reduce_ex", CustomReduceExObject(Pickler.PICKLE_PROTOCOL)),
        SanityTestParams("ellipsis", ...),
    ]


test_sanity_ids, test_sanity_objects, test_sanity_assertions = zip(*[
    (params.test_name, params.test_object, params.should_pass_test)
    for params in create_sanity_test_params()]
)


@pytest.mark.parametrize(
    ['value', 'assertions'],
    zip(test_sanity_objects, test_sanity_assertions),
    ids=test_sanity_ids
)
def test_sanity(value, assertions):
    pickler = Pickler()
    unpickler = Unpickler()
    serialized_value = pickler.pickle(value)
    deserialized_value = unpickler.unpickle(serialized_value)

    assertions(serialized_value, deserialized_value)
