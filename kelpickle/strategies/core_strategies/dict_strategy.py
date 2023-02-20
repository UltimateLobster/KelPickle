from __future__ import annotations
from typing import TYPE_CHECKING, Any

from kelpickle.strategies.base_strategy import BaseStrategy, register_strategy

if TYPE_CHECKING:
    from kelpickle.kelpickling import Pickler, Unpickler


def _reduce_key(key: Any, pickler: Pickler, *, relative_key: str) -> str:
    reduced_key = pickler.reduce(key, relative_key=relative_key)
    assert isinstance(reduced_key, str), "Complex dict keys are not yet supported"
    # TODO: Add support for complex keys
    return reduced_key


@register_strategy(
    name="dict",
    auto_generate_reduction_references=True,
    supported_types=dict,
    consider_subclasses=False
)
class DictStrategy(BaseStrategy):
    def reduce(self, *, instance: dict, pickler: Pickler) -> dict:
        return {
            # TODO: This is just temporary values for the dictionary relative keys. We would need to reconsider them
            #      in order to maintain readability and when reading the result manually as well as consistency between
            #      pickling and unpickling.
            _reduce_key(key, pickler, relative_key=f"{i}_KEY"): pickler.reduce(value, relative_key=str(i))
            for i, (key, value) in enumerate(instance.items())
        }

    def restore_base(self, *, reduced_instance: dict, unpickler: Unpickler) -> dict:
        return {}

    def restore_rest(self, *, reduced_instance: dict, unpickler: Unpickler, base_instance: dict) -> None:
        for i, (key, value) in enumerate(reduced_instance.items()):
            base_instance[unpickler.restore(key, relative_key=f"{i}_KEY")] = unpickler.restore(value, relative_key=str(i))
