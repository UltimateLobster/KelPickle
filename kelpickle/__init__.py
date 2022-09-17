import typing

from kelpickle.common import JsonNative
from kelpickle.strategies.custom_strategies.custom_strategy import (
    restore_with_non_json_strategy,
)
from kelpickle.strategies.internal_strategies.dict_strategy import reduce_dict
from kelpickle.strategies.internal_strategies.internal_strategy import (
    register_unpickling_strategy,
    register_pickling_strategy,
    PicklingStrategy,
    UnpicklingStrategy
)
from kelpickle.strategies.internal_strategies.list_strategy import reduce_list, restore_list
from kelpickle.strategies.internal_strategies.null_strategy import reduce_native, restore_native


# Register all of the basic strategies
register_pickling_strategy(
    PicklingStrategy(reduce_function=reduce_dict, auto_generate_references=True),
    type_to_pickle=dict,
    consider_subclasses=False
)
register_unpickling_strategy(
    UnpicklingStrategy(restore_function=restore_with_non_json_strategy),
    type_to_unpickle=dict
)

register_pickling_strategy(
    PicklingStrategy(reduce_function=reduce_list, auto_generate_references=True),
    type_to_pickle=list,
    consider_subclasses=False,
)
register_unpickling_strategy(
    UnpicklingStrategy(restore_function=restore_list),
    type_to_unpickle=list
)

for native_type in typing.get_args(JsonNative):
    register_pickling_strategy(
        PicklingStrategy(reduce_function=reduce_native, auto_generate_references=False),
        type_to_pickle=native_type,
        consider_subclasses=False
    )
    register_unpickling_strategy(
        UnpicklingStrategy(restore_function=restore_native),
        type_to_unpickle=native_type
    )
