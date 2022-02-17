from datetime import tzinfo, datetime

from kelpickle.common import Json
from kelpickle.pickler import Pickler
from kelpickle.strategies.base_strategy import JsonStrategy
from kelpickle.unpickler import Unpickler

_some_datetime = datetime.now()


class TzInfoStrategy(JsonStrategy[tzinfo]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'tzinfo'

    @staticmethod
    def _flatten(instance: tzinfo, pickler: Pickler) -> Json:
        return {
            'offset': instance.utcoffset(_some_datetime),

        }

    @staticmethod
    def restore(jsonified_object: Json, unpickler: Unpickler) -> tzinfo:
        pass
