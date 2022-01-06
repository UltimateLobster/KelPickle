from __future__ import annotations

from typing import TYPE_CHECKING

from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.pickler import Pickler
    from kelpickle.unpickler import Unpickler


class SetStrategy(BaseStrategy):
    @staticmethod
    def get_strategy_name() -> str:
        return 'set'

    @staticmethod
    def populate_json(instance: set, jsonified_instance: dict[str], pickler: Pickler) -> None:
        jsonified_instance['value'] = [pickler.flatten(member) for member in instance]

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> set:
        return {unpickler.restore(member) for member in jsonified_object['value']}
