from kelpickle.common import NATIVE_TYPES
from kelpickle.kelpickling import restore_reference
from kelpickle.strategies.custom_strategies.custom_strategy import (
    restore_with_non_json_strategy,
    _register_unpickling_strategy_name
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

for native_type in NATIVE_TYPES:
    register_pickling_strategy(
        PicklingStrategy(reduce_function=reduce_native, auto_generate_references=False),
        type_to_pickle=native_type,
        consider_subclasses=False
    )
    register_unpickling_strategy(
        UnpicklingStrategy(restore_function=restore_native),
        type_to_unpickle=native_type
    )

_register_unpickling_strategy_name(
    'reference',
    restore_function=restore_reference,
)

# Import all of the builtin strategies in order to register them
from kelpickle.strategies.custom_strategies.bytes_strategy import BytesStrategy
from kelpickle.strategies.custom_strategies.date_strategy import DateStrategy
from kelpickle.strategies.custom_strategies.datetime_strategy import DatetimeStrategy
from kelpickle.strategies.custom_strategies.import_strategy import ImportStrategy
from kelpickle.strategies.custom_strategies.object_strategy import ObjectStrategy
from kelpickle.strategies.custom_strategies.set_strategy import SetStrategy
from kelpickle.strategies.custom_strategies.time_strategy import TimeStrategy
from kelpickle.strategies.custom_strategies.timedelta_strategy import TimeDeltaStrategy
from kelpickle.strategies.custom_strategies.tuple_strategy import TupleStrategy
from kelpickle.strategies.custom_strategies.tzinfo_strategy import TzInfoStrategy
