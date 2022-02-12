import base64

from kelpickle.pickler import Pickler
from kelpickle.strategies.base_strategy import BaseStrategy, T
from kelpickle.unpickler import Unpickler


class BytesStrategy(BaseStrategy):
    @staticmethod
    def get_strategy_name() -> str:
        return 'base64'

    @staticmethod
    def populate_json(instance: bytes, jsonified_instance: dict[str], pickler: Pickler) -> None:
        jsonified_instance['buffer'] = base64.b64encode(instance).decode('utf-8')

    @staticmethod
    def restore(jsonified_object: dict[str], unpickler: Unpickler) -> bytes:
        return base64.b64decode(jsonified_object['buffer'])
