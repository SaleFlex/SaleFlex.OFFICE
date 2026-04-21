"""Application exception hierarchy for SaleFlex.OFFICE."""


class SaleFlexError(Exception):
    """Root exception for all SaleFlex application errors."""


class DatabaseError(SaleFlexError):
    """Raised when a database operation fails unexpectedly."""

