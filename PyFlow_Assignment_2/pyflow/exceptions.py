"""
Custom exception hierarchy for PyFlow ETL framework.
Question 2: Implement custom exceptions for different error types.
"""


class PyFlowException(Exception):
    """Base exception for all PyFlow errors."""
    pass


class ConfigurationError(PyFlowException):
    """Raised when configuration is invalid or missing."""
    pass


class ExtractionError(PyFlowException):
    """Raised when data extraction fails."""
    pass


class TransformationError(PyFlowException):
    """Raised when data transformation fails."""
    pass


class LoadingError(PyFlowException):
    """Raised when data loading fails."""
    pass


class ValidationError(PyFlowException):
    """Raised when data validation fails."""
    pass


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""
    pass


class DataQualityError(ValidationError):
    """Raised when data quality checks fail."""
    pass


class RetryExhaustedError(PyFlowException):
    """Raised when retry attempts are exhausted."""
    pass
