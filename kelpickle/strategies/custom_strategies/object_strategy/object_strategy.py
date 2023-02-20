from __future__ import annotations

from pickle import DEFAULT_PROTOCOL
from copyreg import __newobj__, __newobj_ex__  # type: ignore
from typing import Any, TypeAlias, cast, TypedDict, Iterable, Callable

from typing_extensions import NotRequired

from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.common import JsonList, Json, Jsonable
from kelpickle.errors import ReductionError
from kelpickle.strategies.custom_strategies.import_strategy import restore_import_string, get_import_string
from kelpickle.kelpickling import Pickler, Unpickler
from kelpickle.strategies.custom_strategies.object_strategy.default_pickling_utils import ImportString, \
    get_containing_module, set_state, PyReduceBuildInstructions, InstanceCreator, \
    InstanceCreatorArguments, DefaultInstanceState, InstanceState, build_list_items_from_reduce, \
    build_dict_items_from_reduce, Instance

DEFAULT_REDUCE = object.__reduce__
DEFAULT_REDUCE_EX = object.__reduce_ex__


class CustomReduceResult(TypedDict):
    reduce: JsonList | ImportString


class CustomStateResult(TypedDict):
    type: ImportString
    state:  NotRequired[Jsonable]
    new_args: NotRequired[JsonList]
    new_kwargs: NotRequired[Json]


ObjectReductionResult: TypeAlias = CustomStateResult | CustomReduceResult


@register_strategy(name='default', supported_types=object, auto_generate_reduction_references=True, consider_subclasses=True)
class ObjectStrategy(BaseStrategy):
    def reduce(self, instance: Any, pickler: Pickler) -> ObjectReductionResult:
        instance_type = instance.__class__
        # The following line assumes there is a valid __reduce_ex__ existing on the instance. Pickle however does an
        # explicit check for that. I'm not sure though if this is relevant anymore (instead of just a python 2
        # compatibility thing. If it turns out it is necessary, I will add the normal pickle behavior
        reduce_result = instance.__reduce_ex__(DEFAULT_PROTOCOL)
        if instance_type.__reduce_ex__ == DEFAULT_REDUCE_EX and instance_type.__reduce__ == DEFAULT_REDUCE:
            # We have no custom implementation of __reduce__/__reduce_ex__. We can use the prettier
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
                                     f"implementation of the reduce protocol yields an unsupported result.",
                                     instance=instance)

            instance_state = reduce_result[2]
            if instance_state is not None:
                result["state"] = pickler.reduce(instance_state, relative_key="state")

            return result

        if isinstance(reduce_result, str):
            # The result is an import string that's missing the module part.
            containing_module = get_containing_module(reduce_result)
            if containing_module is None:
                raise ReductionError(f"Could not pickle object of type {instance_type}. \"{reduce_result}\" is not an "
                                     f"importable name from any module.", instance=instance)

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
            *[pickler.reduce(member, relative_key=str(i))
              for i, member, in enumerate(reduce_result[2:], 2)
              ]
        ]

        return {'reduce': jsonified_result}

    def restore_base(self, reduced_instance: ObjectReductionResult, unpickler: Unpickler) -> Any:
        if "reduce" in reduced_instance:
            reduced_object = cast(CustomReduceResult, reduced_instance)
            flattened_reduce = reduced_object["reduce"]
            if isinstance(flattened_reduce, str):
                return restore_import_string(flattened_reduce)

            if not isinstance(flattened_reduce, list):
                raise TypeError(f"Expected flattened reduce to be a list, received {type(flattened_reduce)}")

            callable_: InstanceCreator = unpickler.restore(flattened_reduce[0], relative_key='0')
            args: InstanceCreatorArguments = unpickler.restore(flattened_reduce[1], relative_key='1')
            return callable_(*args)

        else:
            # Object was not serialized using __reduce__
            reduced_object = cast(CustomStateResult, reduced_instance)
            flattened_instance_type = reduced_object['type']
            instance_type = cast(type, restore_import_string(flattened_instance_type))

            # TODO: Find a way to not restore the args and kwargs if they are not given. Not only will it optimize, it
            #  will also make the custom_strategies not being aware of the pickler's format (Which is arguably even more
            #  important).
            new_args = unpickler.restore(reduced_object.get('new_args', []), relative_key="new_args")
            new_kwargs = unpickler.restore(reduced_object.get('new_kwargs', {}), relative_key="new_kwargs")
            return instance_type.__new__(instance_type, *new_args, **new_kwargs)

    def restore_rest(self, *, reduced_instance: ObjectReductionResult, unpickler: Unpickler, base_instance: Instance) -> None:
        if "reduce" in reduced_instance:
            reduced_object = cast(CustomReduceResult, reduced_instance)
            flattened_reduce = reduced_object["reduce"]
            if isinstance(flattened_reduce, str):
                return

            reduce_result_length = len(flattened_reduce)

            # Restoration has to happen in the following order:
            # 1. Build base instance (Done in the `restore_base` function)
            # 2. Add list items (if defined)
            # 3. Add dict items (if defined)
            # 4. Add state (if defined) and use custom setstate (if defined)
            if reduce_result_length > 3:
                list_items: Iterable[Any] = unpickler.restore(flattened_reduce[3], relative_key='3')
                build_list_items_from_reduce(base_instance, list_items)

            if reduce_result_length > 4:
                dict_items: Iterable[tuple[Any, Any]] = unpickler.restore(flattened_reduce[4], relative_key='4')
                build_dict_items_from_reduce(base_instance, dict_items)

            if reduce_result_length > 2 and flattened_reduce[2]:
                state: DefaultInstanceState | InstanceState = unpickler.restore(flattened_reduce[2], relative_key='2')

                if reduce_result_length > 5:
                    custom_set_state: Callable[[Instance, InstanceState], ...] = unpickler.restore(
                        flattened_reduce[5],
                        relative_key='5'
                    )
                    custom_set_state(base_instance, state)
                else:
                    set_state(base_instance, state)

        else:
            # Object was not serialized using __reduce__
            reduced_object = cast(CustomStateResult, reduced_instance)

            reduced_state = reduced_object.get('state')
            if reduced_state:
                set_state(base_instance, unpickler.restore(reduced_state, relative_key="state"))
