import sys
from typing import TypeAlias, Any, Sequence, Callable, Union, TypeVar, Optional, Iterable

ImportString: TypeAlias = str

Instance = TypeVar("Instance", bound=Any)
InstanceState = TypeVar("InstanceState", bound=Any)
InstanceCreatorArguments = Sequence[Any]
InstanceCreator: TypeAlias = Callable[[InstanceCreatorArguments], Instance]
InstanceDynamicState: TypeAlias = dict[str, Any]
InstanceSlottedState: TypeAlias = dict[str, Any]
DefaultInstanceState: TypeAlias = Union[InstanceDynamicState, tuple[InstanceDynamicState, InstanceSlottedState]]

PyReduceBuildInstructions: TypeAlias = tuple[
    InstanceCreator,
    InstanceCreatorArguments,
    Optional[DefaultInstanceState | InstanceState],
    Optional[Iterable[Any]],
    Optional[Iterable[tuple[str, Any]]],
    Optional[Callable[[Instance, InstanceState], None]]
]

PyReduceResult: TypeAlias = ImportString | PyReduceBuildInstructions


class SetStateError(ValueError):
    pass


def get_containing_module(import_string: str) -> Optional[str]:
    """
    This ugly ass function is a result of pickle supporting weird shit. When a __reduce__/__reduce_ex__ function returns
    a string, that is an import string to be used in the unpickling process. Only problem is, the import string is
    missing the module name. We literally have no way of finding the module name, therefore we need to bruteforce our
    way through 'sys.modules' until we find a module where this is importable (This is literally how pickle does it).

    :param import_string: The import string as returned from the __reduce__/__reduce_ex__ function.
    :return: The import string of the module containing the given object.
    """
    # We need to iterate over a copy of sys.modules because it might be edited as we iterate (additional modules may
    # be dynamically imported as getattr is called)
    for module_name, module in sys.modules.copy().items():
        current_parent = module
        try:
            for import_part in import_string.split("."):
                current_parent = getattr(current_parent, import_part)
        except AttributeError:
            # We didn't manage to import the entire object, that means this module is not the correct one.
            continue

        return module_name

    return None


def _set_dynamic_attributes(instance: Any, dynamic_attributes: dict) -> None:
    for attribute_name, attribute_value in dynamic_attributes.items():
        instance.__dict__[attribute_name] = attribute_value


def _set_slotted_attributes(instance: Any, slotted_attributes: dict[str, Any]) -> None:
    for attribute_name, attribute_value in slotted_attributes.items():
        setattr(instance, attribute_name, attribute_value)


def _default_set_state(instance: Any, state: InstanceState) -> None:
    """
    This is the default way a state is set on an instance if it didn't implement its own __setstate__.

    :param instance: The instance on which we will set the given state.
    :param state: The state of the instance.
    """

    match state:
        case {}:
            _set_dynamic_attributes(instance, state)

        case (dynamic_attributes, slotted_attributes):
            _set_dynamic_attributes(instance, dynamic_attributes or {})
            _set_slotted_attributes(instance, slotted_attributes or {})

        case _:
            raise SetStateError(
                f'Given instance has a state is of type {type(state)}. By default, states may only be a mapping of '
                f'attributes or a tuple of mappings. Make sure the class {type(instance)} has either:\n'
                f'1. Implemented a __getstate__ that returns valid default states.\n'
                f'2. Implemented a __setstate__ that can handle such states\n'
                f'3. Implemented a valid __reduce__/__reduce_ex__.')


def set_state(instance: Any, state: InstanceState) -> None:
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


def build_list_items_from_reduce(instance: Any, list_items: Iterable[Any]):
    try:
        extend = instance.extend
    except AttributeError:
        # If object did not implement the 'extend' method, fallback on 'append' method.
        append = instance.append
        for item in list_items:
            append(item)

    else:
        extend(list_items)


def build_dict_items_from_reduce(instance: Any, dict_items: Iterable[tuple[Any, Any]]):
    for key, value in dict_items:
        instance[key] = value
