"""
Custom Exceptions Module
Defines domain-specific exceptions for web scraping, data cleaning, and analysis.
"""

class CodeAlphaException(Exception):
    """Base exception for all application errors."""
    pass


class ScraperError(CodeAlphaException):
    """Raised when web scraping encounters network, parsing, or HTTP errors."""
    pass


class DataCleaningError(CodeAlphaException):
    """Raised when data transformation or feature engineering fails."""
    pass


class AnalysisError(CodeAlphaException):
    """Raised when statistical analysis or visualization fails."""
    pass
