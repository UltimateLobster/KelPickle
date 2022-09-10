from __future__ import annotations

from types import (
    ModuleType,
    FunctionType,
    WrapperDescriptorType,
    MethodDescriptorType,
    GetSetDescriptorType,
    MemberDescriptorType,
)
from typing import TYPE_CHECKING, Any, Type, TypeAlias

from kelpickle.strategies.custom_strategy import ReductionResult

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


Importable: TypeAlias = (
    Type[Any] |
    FunctionType |
    ModuleType |
    WrapperDescriptorType |
    MethodDescriptorType |
    GetSetDescriptorType |
    MemberDescriptorType
)


def get_import_string(instance: Importable) -> str:
    instance_module = getattr(instance, "__module__", "builtins") or "builtins"
    return f'{instance_module}/{instance.__qualname__}'


def restore_import_string(import_string: str, /) -> Importable:
    module_name, qual_name = import_string.split('/')
    current_object = __import__(module_name, level=0, fromlist=[''])
    for member_name in qual_name.split('.'):
        current_object = getattr(current_object, member_name)

    return current_object


class ImportReductionResult(ReductionResult):
    import_string: str


def reduce_import(instance: Importable, pickler: Pickler) -> ImportReductionResult:
    return {'import_string': get_import_string(instance)}


def restore_import(reduced_object: ImportReductionResult, unpickler: Unpickler) -> Importable:
    return restore_import_string(reduced_object['import_string'])
