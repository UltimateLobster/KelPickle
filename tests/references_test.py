from kelpickle.kelpickling import Pickler, Unpickler
from tests.objects_db import Object, DataClass, FrozenDataClass, CustomStateDataClass, CustomReduceClass, \
    CustomReduceExClass, SlottedClass, SlottedClassWithDynamicDict


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


def test_circular_set():
    pickler = Pickler()
    unpickler = Unpickler()

    circular_set = set()
    circular_set_container = Object(circular_set)
    circular_set.add(circular_set_container)

    serialized = pickler.pickle(circular_set)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is set
    assert len(deserialized) == 1

    deserialized_member = next(iter(deserialized))
    assert type(deserialized_member) is Object
    assert deserialized_member.x is deserialized


def test_circular_list():
    pickler = Pickler()
    unpickler = Unpickler()

    circular_list = []
    circular_list.append(circular_list)

    serialized = pickler.pickle(circular_list)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is list
    assert len(deserialized) == 1
    assert deserialized[0] is deserialized


def test_circular_tuple():
    circular_tuple = (DataClass(1),)
    circular_tuple[0].x = circular_tuple

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_tuple)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_tuple)
    assert len(deserialized) == len(circular_tuple)
    assert deserialized[0] is deserialized


def test_circular_dict():
    circular_dict = {}
    circular_dict["self"] = circular_dict

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_dict)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_dict)
    assert list(deserialized) == list(circular_dict)
    assert deserialized["self"] is deserialized


def test_circular_dataclass():
    circular_dataclass = DataClass(1)
    circular_dataclass.x = circular_dataclass

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_dataclass)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_dataclass)
    assert deserialized.x is deserialized


def test_circular_frozen_dataclass():
    circular_frozen_dataclass = FrozenDataClass(1)
    circular_frozen_dataclass.__dict__["x"] = circular_frozen_dataclass

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_frozen_dataclass)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(serialized)
    assert deserialized.x is deserialized


def test_circular_custom_state_object():
    circular_custom_state_object = CustomStateDataClass(1)
    circular_custom_state_object.x = circular_custom_state_object
    circular_custom_state_object.y = circular_custom_state_object

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_custom_state_object)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_custom_state_object)
    assert deserialized.x is deserialized
    assert deserialized.y is deserialized


def test_circular_custom_reduce_object():
    circular_custom_reduce_object = CustomReduceClass(1)
    circular_custom_reduce_object.x = circular_custom_reduce_object

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_custom_reduce_object)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_custom_reduce_object)
    assert deserialized.x is deserialized


def test_circular_custom_reduce_ex_object():
    circular_custom_reduce_ex_object = CustomReduceExClass(Pickler.PICKLE_PROTOCOL, 1)
    circular_custom_reduce_ex_object.x = circular_custom_reduce_ex_object

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_custom_reduce_ex_object)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_custom_reduce_ex_object)
    assert deserialized.x is deserialized


def test_circular_slotted_object():
    circular_slotted_object = SlottedClass(1)
    circular_slotted_object.x = circular_slotted_object

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_slotted_object)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_slotted_object)
    assert deserialized.x is deserialized


def test_circular_slotted_object_with_dynamic_dict():
    circular_slotted_object_with_dynamic_dict = SlottedClassWithDynamicDict(1, 2)
    circular_slotted_object_with_dynamic_dict.x = circular_slotted_object_with_dynamic_dict
    circular_slotted_object_with_dynamic_dict.y = circular_slotted_object_with_dynamic_dict

    pickler = Pickler()
    unpickler = Unpickler()

    serialized = pickler.pickle(circular_slotted_object_with_dynamic_dict)
    deserialized = unpickler.unpickle(serialized)

    assert type(deserialized) is type(circular_slotted_object_with_dynamic_dict)
    assert deserialized.x is deserialized
    assert deserialized.y is deserialized
