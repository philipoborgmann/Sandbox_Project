"""Expected platform failures."""


class QuontSandboxError(Exception):
    """Base exception for expected platform failures."""


class ConfigurationError(QuontSandboxError):
    """Invalid platform configuration."""


class DataError(QuontSandboxError):
    """Data acquisition, persistence or validity failure."""


class ProviderError(DataError):
    """Provider could not supply the requested data."""


class ValidationError(DataError):
    """Data violates a domain contract."""


class DataNotFoundError(DataError):
    """Requested data does not exist."""
