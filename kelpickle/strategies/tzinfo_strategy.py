from __future__ import annotations
from typing import TYPE_CHECKING, Iterable
from datetime import tzinfo, datetime

from kelpickle.common import Json
from kelpickle.strategies.base_strategy import BaseStrategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler

_some_datetime = datetime.now()


class TzInfoStrategy(BaseStrategy[tzinfo]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'tzinfo'

    @staticmethod
    def get_supported_types() -> Iterable[type]:
        return [tzinfo]

    @staticmethod
    def simplify(instance: tzinfo, pickler: Pickler) -> Json:
        return {
            'offset': instance.utcoffset(_some_datetime),
            'tzinfo': pickler.default_simplify(instance, pickler)
        }

    @staticmethod
    def restore(simplified_object: Json, unpickler: Unpickler) -> tzinfo:
        return unpickler.restore(simplified_object)
