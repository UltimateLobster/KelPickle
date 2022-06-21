from abc import abstractmethod

from kelpickle.common import Jsonable, SimplifiedObject


class BaseFormatter:
    @staticmethod
    @abstractmethod
    def serialize(simplified_instance: SimplifiedObject) -> bytes:
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def deserialize(serialized: bytes) -> SimplifiedObject:
        raise NotImplementedError()
