import base64

from kelpickle.common import Json
from kelpickle.pickler import Pickler
from kelpickle.strategies.base_strategy import BaseStrategy, T
from kelpickle.unpickler import Unpickler


class BytesStrategy(BaseStrategy[bytes]):
    @staticmethod
    def get_strategy_name() -> str:
        return 'base64'

    @staticmethod
    def flatten(instance: T, pickler: Pickler) -> Json:
        return {'buffer': base64.b64encode(instance).decode('utf-8')}

    @staticmethod
    def restore(jsonified_object: dict[str, str], unpickler: Unpickler) -> bytes:
        return base64.b64decode(jsonified_object['buffer'])
