from json import dumps, JSONEncoder
from typing import Any

from kelpickle.common import SimplifiedObject
from kelpickle.formatters.base_formatter import BaseFormatter


class SimplifiedObjectEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if o.simplified_instance



class JsonFormatter(BaseFormatter):
    @staticmethod
    def serialize(simplified_instance: SimplifiedObject) -> bytes:
        if isinstance(simplified_instance.simplified_instance, dict):
            return json.dumps()

        return json.dumps(simplified_instance)

    @staticmethod
    def deserialize(serialized: bytes) -> SimplifiedObject:
        pass
