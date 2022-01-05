from __future__ import annotations

import json

from types import FunctionType, ModuleType
from typing import Any, Callable

from kelpickle.common import NATIVE_TYPES, InstanceState, ReduceResult, null_function, STRATEGY_KEY


class SetStateError(ValueError):
    pass


class Unpickler:
    def __init__(self):
        self.type_to_restore_function: dict[type, Callable] = {
            list: self.restore_by_list,
            dict: self.restore_special_objects,

            **{native_type: null_function for native_type in NATIVE_TYPES}
        }

        self.supported_strategies: dict[str, Callable] = {
            'set': self.restore_by_set,
            'tuple': self.restore_by_tuple,
            'reduce': self.restore_by_reduce,
            'state': self.restore_by_state,
            'import': self.restore_by_import,
            'dict': self.restore_by_dict
        }

    def unpickle(self, serialized_instance):
        return self.restore(json.loads(serialized_instance))

    def restore(self, flattened_instance):
        flattened_instance_type = flattened_instance.__class__
        restorer = self.type_to_restore_function[flattened_instance_type]
        return restorer(flattened_instance)

    def restore_special_objects(self, flattened_instance: dict):
        """
        Restore non-jsonic objects that has to be represented by a dict

        :param flattened_instance: The flattened object to restore
        :return: The original object as was passed to the "flatten" function
        """

        strategy = flattened_instance.get(STRATEGY_KEY, 'dict')
        restore_function = self.supported_strategies[strategy]

        return restore_function(flattened_instance)

    def restore_by_state(self, flattened_instance: dict):
        flattened_instance_type = flattened_instance['type']
        instance_type = self.restore_import_string(flattened_instance_type)
        instance: instance_type = object.__new__(instance_type)

        instance_state = self.restore(flattened_instance['state'])
        self.set_state(instance, instance_state)

        return instance

    def default_set_state(self, instance, state: InstanceState) -> None:
        """
        This is the default way a state is set on an instance if it didn't implement its own __setstate__.

        :param instance: The instance on which we will set the given state.
        :param state: The state of the instance.
        """
        if isinstance(state, dict):
            dynamic_attributes = state
            slotted_attributes = {}

        elif isinstance(state, tuple) and len(state) is 2:
            dynamic_attributes = state[0] or {}
            slotted_attributes = state[1] or {}

        else:
            raise SetStateError(
                f'Given instance has a state is of type {type(state)}. By default, states may only be a mapping of '
                f'attributes or a tuple of mappings. Make sure the class {type(instance)} has either:\n'
                f'1. Implemented a __getstate__ that returns valid default states.\n'
                f'2. Implemented a __setstate__ that can handle such states\n'
                f'3. Implemented a valid __reduce__/__reduce_ex__.')

        # Dynamic attributes are being changed directly through the instance's __dict__ so it won't trigger custom
        # implementations of __setattr__
        instance_dict = instance.__dict__
        for attribute_name, attribute_value in dynamic_attributes.items():
            instance_dict[attribute_name] = attribute_value

        # Unlike dynamic attributes, slotted attributes aren't stored on the instance's __dict__ and therefore can only
        # be set normally
        for attribute_name, attribute_value in slotted_attributes:
            setattr(instance, attribute_name, attribute_value)

    def set_state(self, instance, state: InstanceState) -> None:
        """
        Set the given state on the given instance.

        :param instance:
        :param state:
        """
        try:
            set_state = instance.__setstate__
        except AttributeError:
            self.default_set_state(instance, state)
        else:
            set_state(state)

    def restore_by_reduce(self, flattened_instance: dict):
        flattened_reduce = flattened_instance['value']
        reduce_result = self.restore(flattened_reduce)

        return self.build_from_reduce(reduce_result)

    def build_from_reduce(self, reduce_result: ReduceResult) -> Any:
        """
        Build an instance from the result of a previously called __reduce__/__reduce_ex__.

        Explanation about reduce:
           # TODO: Add explanation here.

        :param reduce_result: The result of __reduce__/__reduce_ex__
        :return: The newly created instance.
        """
        # TODO: Add support for string reduce results
        callable_, args, state, list_items, dict_items, custom_set_state = reduce_result

        # Step 1: Create the instance
        instance = callable_(*args)

        # Step 2: Set the new state
        if state is not None:
            if custom_set_state:
                custom_set_state(instance, state)
            else:
                self.set_state(instance, state)

        # Step 3: Add items
        if list_items is not None:
            try:
                extend = instance.extend
            except AttributeError:
                # If object did not implement the 'extend' method, fallback on 'append' method.
                append = instance.append
                for item in list_items:
                    append(item)

            else:
                extend(list_items)

        # Step 4: Set items
        if dict_items is not None:
            for key, value in dict_items:
                instance[key] = value

        return instance

    def restore_by_list(self, flattened_instance: list):
        return [self.restore(member) for member in flattened_instance]

    def restore_by_dict(self, flattened_instance: dict):
        instance = {}
        for flattened_key, flattened_value in flattened_instance.items():
            instance[self.restore(flattened_key)] = self.restore(flattened_value)

        return instance

    def restore_import_string(self, import_string: str, /):
        module_name, qual_name = import_string.split('/')
        current_object = __import__(module_name, level=0, fromlist=[''])
        for member_name in qual_name.split('.'):
            current_object = getattr(current_object, member_name)

        return current_object

    def restore_by_import(self, flattened_instance: dict, /):
        return self.restore_import_string(flattened_instance['import_string'])

    def restore_by_set(self, flattened_instance: dict) -> set:
        return set(flattened_instance['value'])

    def restore_by_tuple(self, flattened_instance: dict) -> tuple:
        # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
        #  (Use PyTuple_SET)
        return tuple(flattened_instance['value'])
