from __future__ import annotations

from typing import TYPE_CHECKING

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


class SetStrategy(BaseStrategy[set]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'set'

    @staticmethod
    def flatten(instance: set, pickler: Pickler) -> Json:
        return {'value': [pickler.flatten(member) for member in instance]}

    @staticmethod
    def restore(jsonified_object: Json, unpickler: Unpickler) -> set:
        return {unpickler.restore(member) for member in jsonified_object['value']}
