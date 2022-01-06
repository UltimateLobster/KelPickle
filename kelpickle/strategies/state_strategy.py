from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias

from kelpickle.strategies.base_strategy import BaseStrategy, T
from kelpickle.strategies.import_strategy import restore_import_string, get_import_string


if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


InstanceState: TypeAlias = dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]


class SetStateError(ValueError):
    pass


def _default_get_state(instance):
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
    # TODO: Add support for slotted instances.
    return instance.__dict__


def get_state(instance):
    try:
        instance_get_state = instance.__getstate__
    except AttributeError:
        # Instance does not implement __getstate__, so instead of calling it, we will call the default
        # implementation
        return _default_get_state(instance)
    else:
        return instance_get_state()


def _default_set_state(instance, state: InstanceState) -> None:
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


def set_state(instance, state: InstanceState) -> None:
    """
    Set the given state on the given instance.

    :param instance:
    :param state:
    """
    try:
        instance_set_state = instance.__setstate__
    except AttributeError:
        _default_set_state(instance, state)
    else:
        instance_set_state(state)


class StateStrategy(BaseStrategy):
    @staticmethod
    def get_strategy_name() -> str:
        return 'state'

    @staticmethod
    def populate_json(instance: T, jsonified_instance: dict[str], pickler: Pickler) -> None:
        instance_state = get_state(instance)

        jsonified_instance['type'] = get_import_string(instance.__class__)
        jsonified_instance['state'] = pickler.flatten(instance_state)

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> T:
        flattened_instance_type = jsonified_object['type']
        instance_type = restore_import_string(flattened_instance_type)
        instance = object.__new__(instance_type)

        instance_state = unpickler.restore(jsonified_object['state'])
        set_state(instance, instance_state)

        return instance
