from __future__ import annotations

import sys

from pickle import DEFAULT_PROTOCOL
from copyreg import __newobj__, __newobj_ex__  # type: ignore
from typing import Any, Optional, Iterable, Callable, TypeAlias, Type, Sequence, TypeVar, cast, Union, TypedDict

from typing_extensions import NotRequired

from kelpickle.strategies.custom_strategies.custom_strategy import Strategy, register_strategy
from kelpickle.common import JsonList, Json, Jsonable
from kelpickle.errors import ReductionError
from kelpickle.strategies.custom_strategies.import_strategy import restore_import_string, get_import_string
from kelpickle.kelpickling import Pickler, Unpickler

DEFAULT_REDUCE = object.__reduce__
DEFAULT_REDUCE_EX = object.__reduce_ex__


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


class SetStateError(ValueError):
    pass


def _default_set_state(instance: Any, state: InstanceState) -> None:
    """
    This is the default way a state is set on an instance if it didn't implement its own __setstate__.

    :param instance: The instance on which we will set the given state.
    :param state: The state of the instance.
    """
    dynamic_attributes: dict
    slotted_attributes: dict
    if isinstance(state, dict):
        dynamic_attributes = state
        slotted_attributes = {}

    elif isinstance(state, tuple) and len(state) == 2:
        dynamic_attributes = state[0] or {}
        slotted_attributes = state[1] or {}

    else:
        raise SetStateError(
            f'Given instance has a state is of type {type(state)}. By default, states may only be a mapping of '
            f'attributes or a tuple of mappings. Make sure the class {type(instance)} has either:\n'
            f'1. Implemented a __getstate__ that returns valid default states.\n'
            f'2. Implemented a __setstate__ that can handle such states\n'
            f'3. Implemented a valid __reduce__/__reduce_ex__.')

    for attribute_name, attribute_value in dynamic_attributes.items():
        instance.__dict__[attribute_name] = attribute_value

    # Unlike dynamic attributes, slotted attributes aren't stored on the instance's __dict__ and therefore need to
    # be set normally
    for attribute_name, attribute_value in slotted_attributes.items():
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


def build_from_python_reduce(
        callable_: InstanceCreator,
        args: InstanceCreatorArguments,
        state: Optional[InstanceState] = None,
        list_items: Optional[Iterable[Any]] = None,
        dict_items: Optional[Iterable[tuple[str, Any]]] = None,
        custom_set_state: Optional[Callable[[Instance, InstanceState], None]] = None) -> Instance:
    """
    Build an instance from the returned build instructions of a previously called __reduce__/__reduce_ex__. Each
    argument corresponds to the positional member of the build instructions.
    (This obviously should only be called on the non-str results of the python reduce protocol.)

    :param callable_: A callable that will be used in order to create a new instance. This instance may
                      (and probably will) be empty at that point.
    :param args: The arguments that will be passed to the callable.
    :param state: The state of the instance.
    :param list_items: The items of the list that was reduced.
    :param dict_items: The items of the dict that was reduced.
    :param custom_set_state: A function that will be called to set the state of the instance.
    :return: The newly created instance.
    """

    # Step 1: Create the instance
    instance: Instance = callable_(*args)

    # Step 2: Extend items (relevant only for list subclasses, should happen before setting state)
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

    # Step 3: Extend keyword items (relevant only for dict subclasses, should happen before setting state)
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


class CustomReduceResult(TypedDict):
    reduce: JsonList | ImportString


class CustomStateResult(TypedDict):
    type: ImportString
    state:  NotRequired[Jsonable]
    new_args: NotRequired[JsonList]
    new_kwargs: NotRequired[Json]


ObjectReductionResult: TypeAlias = CustomStateResult | CustomReduceResult


@register_strategy('python_object', supported_types=object, consider_subclasses=True)
class ObjectStrategy(Strategy):
    @staticmethod
    def reduce(instance: Any, pickler: Pickler) -> ObjectReductionResult:
        instance_type = instance.__class__
        # The following line assumes there is a valid __reduce_ex__ existing on the instance. Pickle however does an
        # explicit check for that. I'm not sure though if this is relevant anymore (instead of just a python 2
        # compatibility thing. If it turns out it is necessary, I will add the normal pickle behavior
        reduce_result = instance.__reduce_ex__(DEFAULT_PROTOCOL)
        if instance_type.__reduce_ex__ == DEFAULT_REDUCE_EX and instance_type.__reduce__ == DEFAULT_REDUCE:
            # We have no custom_strategies implementation of __reduce__/__reduce_ex__. We can use the prettier
            # representation of the object
            reduce_result = cast(PyReduceBuildInstructions, reduce_result)
            result: CustomStateResult = {
                "type": get_import_string(instance_type)
            }

            if reduce_result[0] == __newobj_ex__:
                _, new_args, new_kwargs = reduce_result[1]
                if new_args:
                    result["new_args"] = cast(JsonList, pickler.reduce(new_args, relative_key="new_args"))

                if new_kwargs:
                    result["new_kwargs"] = cast(Json, pickler.reduce(new_kwargs, relative_key="new_kwargs"))

            elif reduce_result[0] == __newobj__:
                _, *new_args = reduce_result[1]
                if new_args:
                    result["new_args"] = cast(JsonList, pickler.reduce(new_args, relative_key="new_args"))

            else:
                raise ReductionError(f"Instance of type {instance_type} cannot be pickled. The default "
                                     f"implementation of the reduce protocol yields an unsupported result.")

            instance_state = reduce_result[2]
            if instance_state is not None:
                result["state"] = pickler.reduce(instance_state, relative_key="state")

            return result

        if isinstance(reduce_result, str):
            # The result is an import string that's missing the module part.
            containing_module = get_containing_module(reduce_result)
            if containing_module is None:
                raise ReductionError(f"Could not pickle object of type {type(instance)} with use_python_reduce result "
                                     f"{reduce_result}, it is not importable from any module.")

            return {'reduce': f"{containing_module}/{reduce_result}"}

        # TODO: Reconsider to somehow put a "reduce" relative key before accessing each member with its own relative
        #  key.
        callable_ = reduce_result[0]
        # This is done so the args part will be more readable (just a list instead of a json created from the tuple
        # strategy).
        args = list(reduce_result[1])

        jsonified_result = [
            pickler.reduce(callable_, relative_key="0"),
            pickler.reduce(args, relative_key="1"),
            *[pickler.reduce(x, relative_key=str(i))
              for i, x, in enumerate(reduce_result[2:], 2)
              ]
        ]

        return {'reduce': jsonified_result}

    @staticmethod
    def restore(reduced_object: ObjectReductionResult, unpickler: Unpickler) -> Any:
        if "reduce" in reduced_object:
            reduced_object = cast(CustomReduceResult, reduced_object)
            flattened_reduce = reduced_object["reduce"]
            if isinstance(flattened_reduce, str):
                return restore_import_string(flattened_reduce)

            assert isinstance(flattened_reduce,
                              list), f"Expected flattened reduce to be a list, received {type(flattened_reduce)}"

            # TODO: type this in a better way
            reduce_result: PyReduceBuildInstructions = tuple(  # type: ignore
                unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(flattened_reduce)
            )
            return build_from_python_reduce(*reduce_result)

        else:
            # Object was not serialized using __reduce__
            reduced_object = cast(CustomStateResult, reduced_object)
            flattened_instance_type = reduced_object['type']
            instance_type = cast(type, restore_import_string(flattened_instance_type))

            # TODO: Find a way to not restore the args and kwargs if they are not given. Not only will it optimize, it
            #  will also make the custom_strategies not being aware of the pickler's format (Which is arguably even more
            #  important).
            new_args = unpickler.restore(reduced_object.get('new_args', []), relative_key="new_args")
            new_kwargs = unpickler.restore(reduced_object.get('new_kwargs', {}), relative_key="new_kwargs")
            instance = instance_type.__new__(instance_type, *new_args, **new_kwargs)

            reduced_state = reduced_object.get('state')
            if reduced_state:
                set_state(instance, unpickler.restore(reduced_state, relative_key="state"))

            return instance
