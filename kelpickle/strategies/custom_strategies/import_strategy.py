from __future__ import annotations

from types import (
    ModuleType,
    FunctionType,
    WrapperDescriptorType,
    MethodDescriptorType,
    GetSetDescriptorType,
    MemberDescriptorType,
)
from typing import Any, Type, TypeAlias, TypedDict

from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy
from kelpickle.kelpickling import Pickler, Unpickler

Importable: TypeAlias = (
    Type[Any] |
    FunctionType |
    WrapperDescriptorType |
    MethodDescriptorType |
    GetSetDescriptorType |
    MemberDescriptorType
)


def get_import_string(instance: Importable) -> str:
    if isinstance(instance, ModuleType):
        return instance.__name__

    instance_module = getattr(instance, "__module__", "builtins") or "builtins"
    return f'{instance_module}/{instance.__qualname__}'


def restore_import_string(import_string: str, /) -> Importable:
    module_name, *rest = import_string.split('/')
    current_object = __import__(module_name, level=0, fromlist=[''])
    if rest:
        for member_name in rest[0].split('.'):
            current_object = getattr(current_object, member_name)

    return current_object


class ImportReductionResult(TypedDict):
    import_string: str


@register_strategy(
    name='import',
    supported_types=(
            type,
            FunctionType,
            WrapperDescriptorType,
            MethodDescriptorType,
            GetSetDescriptorType,
            MemberDescriptorType
    ),
    auto_generate_reduction_references=False,
    consider_subclasses=False
)
class ImportStrategy(BaseStrategy):
    def reduce(self, instance: Importable, pickler: Pickler) -> ImportReductionResult:
        return {'import_string': get_import_string(instance)}

    def restore_base(self, reduced_instance: ImportReductionResult, unpickler: Unpickler) -> Importable:
        return restore_import_string(reduced_instance['import_string'])
