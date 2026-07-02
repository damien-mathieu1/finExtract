class FinExtractError(Exception):
    """Base class for all domain-level errors in FinExtract."""


class SourceNotFoundError(FinExtractError):
    """Raised when a requested filing/source cannot be located or fetched."""


class UnmappableTagError(FinExtractError):
    """Raised when a taxonomy tag has no known mapping to the standard schema."""
