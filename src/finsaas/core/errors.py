"""Custom exception hierarchy for FinSaaS."""


class FinSaaSError(Exception):
    """Base exception for all FinSaaS errors."""


class SeriesError(FinSaaSError):
    """Error related to Series operations."""


class SeriesIndexError(SeriesError):
    """Accessing a Series index that doesn't exist yet."""


class InsufficientDataError(SeriesError):
    """Not enough bars to compute an indicator."""


class StrategyError(FinSaaSError):
    """Error in strategy definition or execution."""


class ParameterError(StrategyError):
    """Invalid strategy parameter value."""


class OrderError(FinSaaSError):
    """Error in order processing."""


class InsufficientCapitalError(OrderError):
    """Not enough capital to place an order."""


class RiskLimitError(OrderError):
    """Order rejected by risk controls."""


class DataError(FinSaaSError):
    """Error in data loading or access."""


class DataNotFoundError(DataError):
    """Requested data not found."""


class DataIntegrityError(DataError):
    """Data integrity issue (gaps, duplicates)."""


class PineScriptError(FinSaaSError):
    """Error in Pine Script parsing or transpilation."""


class PineSyntaxError(PineScriptError):
    """Pine Script syntax error."""


class PineSemanticError(PineScriptError):
    """Pine Script semantic error (type mismatch, undefined variable)."""


class PineRuntimeError(PineScriptError):
    """Pine Script runtime error."""


class OptimizationError(FinSaaSError):
    """Error during optimization."""


class ConfigError(FinSaaSError):
    """Configuration error."""
