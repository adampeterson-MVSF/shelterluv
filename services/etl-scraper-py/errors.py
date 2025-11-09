class EtlError(Exception):
    """Custom exception for ETL failures."""
    pass


class ApiError(EtlError):
    """Error related to ShelterLuv API calls."""
    pass


class ScraperError(EtlError):
    """Error related to web scraping operations."""
    pass


class SchemaValidationError(EtlError):
    """Error related to JSON schema validation."""
    pass
