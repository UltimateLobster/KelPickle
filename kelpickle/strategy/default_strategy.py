from __future__ import annotations

import sys
from pickle import DEFAULT_PROTOCOL
from typing import Any, TYPE_CHECKING, Optional, Iterable, Callable, TypeAlias, Type, Sequence, TypeVar
import copyreg

from kelpickle.common import JsonList, PicklingError
from kelpickle.strategy.base_strategy import BaseNonNativeJsonStrategy, JsonicReductionResult, ReductionResult
from kelpickle.strategy.import_strategy import restore_import_string, get_import_string

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


DEFAULT_REDUCE = object.__reduce__
DEFAULT_REDUCE_EX = object.__reduce_ex__


ImportString: TypeAlias = str

Instance = TypeVar("Instance", bound=Any)
InstanceState = TypeVar("InstanceState", bound=Any)
InstanceCreatorArguments = Sequence[Any]
InstanceCreator: TypeAlias = Callable[[InstanceCreatorArguments], Instance]
DefaultInstanceState: TypeAlias = dict[str, Any] | tuple[dict[str, Any], dict[str, Any]]

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
        dict_items: Optional[Iterable[Sequence[str, Any]]] = None,
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
    instance = callable_(*args)

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


def use_python_reduce(instance: Any) -> PyReduceResult:
    reduce_func: Callable[[int], PyReduceResult]
    if reduce_func := getattr(instance, "__reduce_ex__", None):
        return reduce_func(DEFAULT_PROTOCOL)

    reduce_ex_func: Callable[..., PyReduceResult]
    if reduce_ex_func := getattr(instance, "__reduce__", None):
        return reduce_ex_func()

    raise PicklingError(f'Instance of type {type(instance)} cannot be pickled. It does not implement the reduce '
                        f'protocol.', instance)


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
        reduce_result = use_python_reduce(instance)
        if instance_type.__reduce_ex__ == DEFAULT_REDUCE_EX and instance_type.__reduce__ == DEFAULT_REDUCE:
            # We have no custom implementation of __reduce__/__reduce_ex__. We can use the prettier representation of
            # the object
            result = {
                'type': get_import_string(instance.__class__),
            }

            match reduce_result:
                case copyreg.__newobj_ex__, (_, new_args, new_kwargs), *_:
                    if new_args:
                        result["new_args"] = pickler.reduce(new_args, relative_key="new_args")

                    if new_kwargs:
                        result["new_kwargs"] = pickler.reduce(new_kwargs, relative_key="new_kwargs")

                case copyreg.__newobj__, (_, *new_args), *_:
                    if new_args:
                        result["new_args"] = pickler.reduce(new_args, relative_key="new_args")

                case _:
                    raise PicklingError(f"Instance of type {instance_type} cannot be pickled. The default "
                                        f"implementation of the reduce protocol yields an unsupported result.")

            instance_state = reduce_result[2]
            if instance_state is not None:
                result['state'] = pickler.reduce(instance_state, relative_key="state")

            return result

        if isinstance(reduce_result, str):
            # The result is an import string that's missing the module part.
            containing_module = get_containing_module(reduce_result)
            if containing_module is None:
                raise PicklingError(f"Could not pickle object of type {type(instance)} with use_python_reduce result "
                                    f"{reduce_result}, it is not importable from any module.")

            return {'reduce': f"{containing_module}/{reduce_result}"}

        # TODO: Reconsider to somehow put a "reduce" relative key before accessing each member with its own relative
        #  key.
        # Ugly patch here. We're translating the args part of the tuple to a list. This is done so the args part will
        # be more readable (just a list instead of a json with a tuple strategy). Should matter but we'll see.
        jsonified_result = [
            pickler.reduce(list(x), relative_key=str(i)) if i == 1 else pickler.reduce(x, relative_key=str(i))
            for i, x in enumerate(reduce_result)
        ]

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
            new_args = unpickler.restore(reduced_object.get('new_args', []), relative_key="new_args")
            new_kwargs = unpickler.restore(reduced_object.get('new_kwargs', {}), relative_key="new_kwargs")
            instance = instance_type.__new__(instance_type, *new_args, **new_kwargs)

            instance_state = unpickler.restore(reduced_object.get('state'), relative_key="state")
            if instance_state is not None:
                set_state(instance, instance_state)

            return instance

        if isinstance(flattened_reduce, str):
            return restore_import_string(flattened_reduce)

        # TODO: type this in a better way
        reduce_result: PyReduceBuildInstructions = tuple(
            unpickler.restore(member, relative_key=str(i)) for i, member in enumerate(flattened_reduce))  # type: ignore
        return build_from_python_reduce(*reduce_result)
