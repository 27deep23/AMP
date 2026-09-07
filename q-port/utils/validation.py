"""
Validation utilities and custom exception classes for Q-PORT.
Ensures specific, structured error reporting for infeasible optimization configurations.
"""

class QPortError(Exception):
    """Base exception for Q-PORT platform."""
    pass


class InfeasibleConstraintError(QPortError):
    """Raised when user-specified constraints are mathematically impossible to satisfy."""
    pass


class InvalidParameterError(QPortError):
    """Raised when input parameters are out of allowed bounds or malformed."""
    pass


class DataQualityError(QPortError):
    """Raised when dataset quality is insufficient for portfolio optimization."""
    pass


class ComputationTimeoutError(QPortError):
    """Raised when an algorithm exceeds designated wall-clock execution limits."""
    pass
