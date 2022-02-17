from __future__ import annotations

from types import FunctionType, ModuleType
from typing import TYPE_CHECKING, Any, Type, TypeAlias

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import JsonStrategy

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


Importable: TypeAlias = Type[Any] | FunctionType | ModuleType


def get_import_string(instance: Importable) -> str:
    return f'{instance.__module__}/{instance.__qualname__}'


def restore_import_string(import_string: str, /) -> Importable:
    module_name, qual_name = import_string.split('/')
    current_object = __import__(module_name, level=0, fromlist=[''])
    for member_name in qual_name.split('.'):
        current_object = getattr(current_object, member_name)

    return current_object


class ImportStrategy(JsonStrategy[Importable]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'import'

    @staticmethod
    def _flatten(instance: Importable, pickler: Pickler) -> Json:
        return {'import_string': get_import_string(instance)}

    @staticmethod
    def restore(jsonified_object: Json, unpickler: Unpickler) -> Importable:
        return restore_import_string(jsonified_object['import_string'])
