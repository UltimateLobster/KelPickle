from __future__ import annotations

import json

from typing import Callable
from pickle import DEFAULT_PROTOCOL
from kelpickle.common import NATIVE_TYPES, ReduceResult, null_function


class PicklingError(Exception):
    """
    Error that occurs during the pickling process
    """
    pass


class Pickler:
    def __init__(self):
        self.type_to_restore_function: dict[type, Callable] = {
            list: self.flatten_by_list,
            dict: self.flatten_by_dict,
            type: self.flatten_by_type,
            set: self.flatten_by_set,
            tuple: self.flatten_by_tuple,
            **{native_type: null_function for native_type in NATIVE_TYPES}
        }

    def pickle(self, instance):
        return json.dumps(self.flatten(instance))

    def flatten(self, instance):
        instance_type = instance.__class__
        flattener = self.type_to_restore_function.get(instance_type, self.default_flatten)

        return flattener(instance)

    def default_get_state(self, instance):
        """
        This is the default way to return an object's state if it didn't implement its own custom __getstate__.

        By default, objects' state will be a mapping between a mapping between attribute names and values. Slotted
        objects (instances of classes that implemented __slots__) will have an additional mapping specifically for the
        slotted attributes. Such objects will have a tuple containing both of the mappings (A slotted object can have
        __dict__ as one of the slotted attributes in which case it can have a combination of dynamic and static
        namespace).

        :param instance: The instance whose state shall be returned.
        :return: The given instance's state.
        """
        return instance.__dict__

    def default_flatten(self, instance):
        instance_class = type(instance)
        # TODO: Make this whole thing beautiful, its fucking stupid that you need to reference __reduce__ and
        #  __reduce_ex__ in multiple places and its ugly as fuck.
        if instance_class.__reduce_ex__ is object.__reduce_ex__ and instance_class.__reduce__ is object.__reduce__:
            # Instance did not implement a custom reduce. That means we may implement a syntactic sugar and flatten our
            # instance differently
            return self.flatten_by_state(instance)

        return self.flatten_by_reduce(instance)

    def flatten_by_reduce(self, instance):
        reduce = getattr(instance, "__reduce_ex__", None)
        if reduce:
            return self.flatten_reduce_result(reduce(DEFAULT_PROTOCOL))

        reduce = getattr(instance, "__reduce__", None)
        if reduce:
            return self.flatten_reduce_result(reduce())

        raise PicklingError(f'Instance of type {type(instance)} cannot be pickled. It does not implement the reduce '
                            f'protocol.', instance)

    def flatten_reduce_result(self, reduce_result: ReduceResult):
        flattened_result = [self.flatten(x) for x in reduce_result]
        flattened_result.extend([None] * (6 - len(flattened_result)))

        return {'py/reduce': flattened_result}

    def flatten_by_state(self, instance):
        try:
            instance_get_state = instance.__getstate__
        except AttributeError:
            # Instance does not implement __getstate__, so instead of calling it, we will call the default
            # implementation
            instance_state = self.default_get_state(instance)
        else:
            instance_state = instance_get_state()

        return {
            'py/object': self.flatten(instance.__class__),
            'py/state': self.flatten(instance_state)
        }

    def flatten_by_list(self, instance: list) -> list:
        return [self.flatten(member) for member in instance]

    def flatten_by_dict(self, instance: dict) -> dict:
        flattened_instance = {}
        for key, value in instance.items():
            flattened_instance[self.flatten(key)] = self.flatten(value)

        return flattened_instance

    def flatten_by_type(self, instance: type) -> str:
        return f'{instance.__module__}/{instance.__qualname__}'

    def flatten_by_set(self, instance: set) -> dict:
        return {'py/set': list(instance)}

    def flatten_by_tuple(self, instance: tuple) -> dict:
        return {'py/tuple': instance}
