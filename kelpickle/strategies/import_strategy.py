from __future__ import annotations

from typing import TYPE_CHECKING
from kelpickle.strategies.base_strategy import BaseStrategy, T

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


def get_import_string(instance) -> str:
    return f'{instance.__module__}/{instance.__qualname__}'


def restore_import_string(import_string: str, /):
    module_name, qual_name = import_string.split('/')
    current_object = __import__(module_name, level=0, fromlist=[''])
    for member_name in qual_name.split('.'):
        current_object = getattr(current_object, member_name)

    return current_object


class ImportStrategy(BaseStrategy):
    @staticmethod
    def get_strategy_name() -> str:
        return 'import'

    @staticmethod
    def populate_json(instance: T, jsonified_instance: dict[str], pickler: Pickler) -> None:
        jsonified_instance['import_string'] = get_import_string(instance)

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> T:
        return restore_import_string(jsonified_object['import_string'])
