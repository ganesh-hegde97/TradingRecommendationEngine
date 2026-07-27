class TradingEngineException(Exception):
    """Base exception for the application."""


class MarketDataException(TradingEngineException):
    """Market data download failure."""


class InvalidSymbolException(TradingEngineException):
    """Invalid stock symbol."""


class RecommendationException(TradingEngineException):
    """Recommendation generation failure."""


class ExportException(TradingEngineException):
    """Excel export failure."""


class ValidationException(TradingEngineException):
    """Invalid user input."""
