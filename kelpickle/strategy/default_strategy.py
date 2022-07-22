from __future__ import annotations

import sys
from pickle import DEFAULT_PROTOCOL
from typing import Any, TYPE_CHECKING, Optional, Iterable, Callable, TypeAlias, Type

from kelpickle.common import JsonList
from kelpickle.strategy.base_strategy import BaseNonNativeJsonStrategy, JsonicReductionResult, ReductionResult
from kelpickle.strategy.import_strategy import restore_import_string, get_import_string

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


DEFAULT_REDUCE = object.__reduce__
DEFAULT_REDUCE_EX = object.__reduce_ex__


ImportString: TypeAlias = str
InstanceState: TypeAlias = dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]
PyReduceBuildInstructions: TypeAlias = tuple[
    Callable,
    Iterable,
    Optional[InstanceState | Any],
    Optional[Iterable],
    Optional[Iterable[tuple[str, Any]]],
    Optional[Callable[[Any, InstanceState], None]]
]

PyReduceResult: TypeAlias = ImportString | PyReduceBuildInstructions


class UnreducableObject(ValueError):
    pass


class PyReduceError(ValueError):
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


def use_python_reduce(instance: Any) -> PyReduceResult:
    reduce_func: Callable[[int], PyReduceResult]
    if reduce_func := getattr(instance, "__reduce_ex__", None):
        return reduce_func(DEFAULT_PROTOCOL)

    reduce_ex_func: Callable[..., PyReduceResult]
    if reduce_ex_func := getattr(instance, "__reduce__", None):
        return reduce_ex_func()

    raise UnreducableObject(f'Instance of type {type(instance)} cannot be pickled. It does not implement the reduce '
                            f'protocol.', instance)


def build_from_pyreduce(reduce_result: PyReduceBuildInstructions) -> Any:
    """
    Build an instance from the non-str result of a previously called __reduce__/__reduce_ex__.

    Explanation about python's reduce:
       # TODO: Add explanation here.

    :param reduce_result: The result of __reduce__/__reduce_ex__
    :return: The newly created instance.
    """
    # TODO: Add support for string use_python_reduce results
    callable_, args, state, list_items, dict_items, custom_set_state = reduce_result

    # Step 1: Create the instance
    instance = callable_(*args)

    # Step 2: Add items
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

    # Step 3: Set items
    if dict_items is not None:
        for key, value in dict_items:
            instance[key] = value

    # Step 4: Set the new state
    if state is not None:
        if custom_set_state:
            custom_set_state(instance, state)
        else:
            set_state(instance, state)

    return instance


class SetStateError(ValueError):
    pass


def _default_get_state(instance: Any) -> dict:
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
    return getattr(instance, "__dict__", None)


def get_state(instance: Any) -> Any:
    try:
        custom_getstate: Callable[..., Any] = instance.__getstate__
    except AttributeError:
        # Instance does not implement __getstate__, so instead of calling it, we will call the default
        # implementation
        return _default_get_state(instance)
    else:
        return custom_getstate()


def get_custom_newargs(instance: Any) -> tuple[Optional[tuple], Optional[dict]]:
    try:
        getnewargs_ex: Callable[[], tuple[tuple, dict]] = instance.__getnewargs_ex__
    except AttributeError:
        try:
            getnewargs: Callable[[], tuple] = instance.__getnewargs__
        except AttributeError:
            return None, None
        else:
            return getnewargs(), None
    else:
        return getnewargs_ex()


def _default_set_state(instance: Any, state: InstanceState) -> None:
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


class DefaultReductionResult(JsonicReductionResult):
    reduce: JsonList | ImportString
    type: ImportString
    state: ReductionResult


class DefaultStrategy(BaseNonNativeJsonStrategy[Any, DefaultReductionResult]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'python_object'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [object]

    @staticmethod
    def reduce(instance: Any, pickler: Pickler) -> DefaultReductionResult:
        instance_type = instance.__class__
        if instance_type.__reduce_ex__ == DEFAULT_REDUCE_EX and instance_type.__reduce__ == DEFAULT_REDUCE:
            # We have no custom implementation of __reduce__/__reduce_ex__. We can use the prettier representation of
            # the object
            result = {
                'type': get_import_string(instance.__class__),
            }

            new_args, new_kwargs = get_custom_newargs(instance)

            if new_args is not None:
                result["new_args"] = pickler.reduce(new_args)

            if new_kwargs is not None:
                result["new_kwargs"] = pickler.reduce(new_kwargs)

            instance_state = get_state(instance)
            if instance_state is not None:
                result['state'] = pickler.reduce(instance_state)

            return result

        reduce_result = use_python_reduce(instance)
        if isinstance(reduce_result, str):
            # The result is an import string that's missing the module part.
            containing_module = get_containing_module(reduce_result)
            if containing_module is None:
                raise PyReduceError(f"Could not pickle object of type {type(instance)} with use_python_reduce result {reduce_result}"
                                  f", it is not importable from any module.")

            return {'reduce': f"{containing_module}/{reduce_result}"}

        jsonified_result = [pickler.reduce(x) for x in reduce_result]
        none_padding: JsonList = [None] * (6 - len(jsonified_result))
        jsonified_result.extend(none_padding)

        return {'reduce': jsonified_result}

    @staticmethod
    def restore(reduced_object: DefaultReductionResult, unpickler: Unpickler) -> Any:
        flattened_reduce = reduced_object.get('reduce')
        if flattened_reduce is None:
            # Object was not serialized using pyreduce.
            flattened_instance_type = reduced_object['type']
            instance_type: Type[Any] = restore_import_string(flattened_instance_type)

            # TODO: Find a way to not restore the args and kwargs if they are not given. Not only will it optimize, it
            #  will also make the strategy not being aware of the pickler's format (Which is arguably even more
            #  important).
            new_args = unpickler.restore(reduced_object.get('new_args', []))
            new_kwargs = unpickler.restore(reduced_object.get('new_kwargs', {}))
            instance = instance_type.__new__(instance_type, *new_args, **new_kwargs)

            instance_state = unpickler.restore(reduced_object.get('state'))
            if instance_state is not None:
                set_state(instance, instance_state)

            return instance

        if isinstance(flattened_reduce, str):
            return restore_import_string(flattened_reduce)

        # TODO: type this in a better way
        reduce_result: PyReduceBuildInstructions = tuple(
            unpickler.restore(member) for member in flattened_reduce)  # type: ignore
        return build_from_pyreduce(reduce_result)
