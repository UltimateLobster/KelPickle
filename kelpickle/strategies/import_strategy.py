from __future__ import annotations

from types import (
    ModuleType,
    FunctionType,
    BuiltinFunctionType,
    BuiltinMethodType,
    WrapperDescriptorType,
    MethodWrapperType,
    MethodDescriptorType,
    ClassMethodDescriptorType,
    GetSetDescriptorType,
    MemberDescriptorType
)
from typing import TYPE_CHECKING, Any, Type, TypeAlias, Iterable

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


Importable: TypeAlias = Type[Any] | FunctionType | ModuleType


def get_import_string(instance: Importable) -> str:
    return f'{instance.__module__}/{instance.__qualname__}'


def restore_import_string(import_string: str, /) -> Importable:
    module_name, qual_name = import_string.split('/')
    current_object = __import__(module_name, level=0, fromlist=[''])
    for member_name in qual_name.split('.'):
        current_object = getattr(current_object, member_name)

    return current_object


class ImportStrategy(BaseStrategy[Importable]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'import'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [
            type,
            ModuleType,
            FunctionType,
            BuiltinFunctionType,
            BuiltinMethodType,
            WrapperDescriptorType,
            MethodWrapperType,
            MethodDescriptorType,
            ClassMethodDescriptorType,
            GetSetDescriptorType,
            MemberDescriptorType
        ]

    @staticmethod
    def simplify(instance: Importable, pickler: Pickler) -> Json:
        return {'import_string': get_import_string(instance)}

    @staticmethod
    def restore(simplified_object: Json, unpickler: Unpickler) -> Importable:
        return restore_import_string(simplified_object['import_string'])
