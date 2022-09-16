class PicklingError(Exception):
    """
    Error that occurs during the pickling process
    """
    pass


class UnpicklingError(Exception):
    """
    Error that occurs during the unpickling process
    """
    pass


class UnsupportedStrategy(UnpicklingError):
    """
    Error that occurs if encountered an object that was pickled using an unsupported custom_strategies
    """
    pass
