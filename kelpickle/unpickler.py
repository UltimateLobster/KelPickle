from __future__ import annotations

import json

from typing import Any, Callable

from kelpickle.common import NATIVE_TYPES, InstanceState, ReduceResult, null_function


class Unpickler:
    def __init__(self):
        self.type_to_restore_function: dict[type, Callable] = {
            list: self.restore_by_list,
            type: self.restore_by_type,
            dict: self.restore_special_objects,

            **{native_type: null_function for native_type in NATIVE_TYPES}
        }

    def unpickle(self, serialized_instance):
        return self.restore(json.loads(serialized_instance))

    def restore(self, flattened_instance):
        flattened_instance_type = flattened_instance.__class__
        restorer = self.type_to_restore_function[flattened_instance_type]
        return restorer(flattened_instance)

    def restore_special_objects(self, flattened_instance: dict):
        """
        Restore objects that cannot be naively flattened as jsonic dicts.

        :param flattened_instance: The flattened object to restore
        :return: The original object as was passed to the "flatten" function
        """
        if 'py/set' in flattened_instance:
            return self.restore_by_set(flattened_instance)

        if 'py/tuple' in flattened_instance:
            return self.restore_by_tuple(flattened_instance)

        if 'py/reduce' in flattened_instance:
            return self.restore_by_reduce(flattened_instance)

        if 'py/object' in flattened_instance:
            return self.restore_by_state(flattened_instance)

        return self.restore_by_dict(flattened_instance)

    def restore_by_state(self, flattened_instance: dict):
        flattened_instance_type = flattened_instance['py/object']
        instance_type = self.restore_by_type(flattened_instance_type)
        instance: instance_type = object.__new__(instance_type)

        instance_state = flattened_instance['py/state']
        self.set_state(instance, instance_state)

        return instance


    def default_set_state(self, instance, state: InstanceState) -> None:
        """
        This the default way a state is set on an instance if it didn't implement its own __setstate__.

        :param instance: The instance on which we will set the given state.
        :param state: The state of the instance.
        """
        slot_state = {}

        if isinstance(state, tuple):
            state, slot_state = state

        instance_dict = instance.__dict__
        for key, value in state.items():
            instance_dict[key] = value

        for key, value in slot_state:
            setattr(instance, key, value)

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
        flattened_reduce = flattened_instance.get('py/reduce')
        if flattened_reduce:
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

    def restore_by_type(self, flattened_instance: str) -> type:
        module_name, qual_name = flattened_instance.split('/')
        current_object = __import__(module_name, level=0, fromlist=[''])
        for member_name in qual_name.split('.'):
            current_object = getattr(current_object, member_name)

        return current_object

    def restore_by_set(self, flattened_instance: dict) -> set:
        return set(flattened_instance['py/set'])

    def restore_by_tuple(self, flattened_instance: dict) -> tuple:
        # TODO: Create the tuple one member at a time so you can record reference of the set beforehand
        #  (Use PyTuple_SET)
        return tuple(flattened_instance['py/tuple'])
