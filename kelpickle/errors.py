from typing import Any


class PicklingError(Exception):
    """
    Error that occurs during the pickling process
    """
    def __init__(self, message: str, *, instance: Any):
        super(f"During the pickling process of {instance}. The following error has occurred: {message}")
        self.instance = instance


class ReductionError(PicklingError):
    """
    Error that occurs during the reduce stage of the pickling process
    """


class ReductionReferenceCollision(ReductionError):
    """
    Error that occurs when more than one instances try to be recorded under the same reference
    """


class UnpicklingError(Exception):
    """
    Error that occurs during the unpickling process
    """


class RestoreError(UnpicklingError):
    """
    Error that occurs when the restoration process cannot be completed
    """


class UnsupportedStrategy(RestoreError):
    """
    Error that occurs if tried to restore an object that was pickled using an unsupported strategy
    """


class RestorationReferenceCollision(RestoreError):
    """
    Error that occurs when during the restoration process, multiple instances tried to be recorded under the same
    reference name
    """


class StrategyConflictError(ValueError):
    pass


class DuplicateStrategyNameError(StrategyConflictError):
    pass


class UnsupportedPicklingType(TypeError):
    pass

