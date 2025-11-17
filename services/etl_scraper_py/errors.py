class EtlError(Exception):
    """Custom exception for ETL failures."""

    def __str__(self) -> str:
        return f"ETL Error: {self.args[0] if self.args else ''}"


class ApiError(EtlError):
    """Error related to ShelterLuv API calls."""

    def __str__(self) -> str:
        return f"API Error: {self.args[0] if self.args else ''}"


class ScraperError(EtlError):
    """Error related to web scraping operations."""

    def __str__(self) -> str:
        return f"Scraper Error: {self.args[0] if self.args else ''}"


class SchemaValidationError(EtlError):
    """Error related to JSON schema validation."""

    def __str__(self) -> str:
        return f"Schema Validation Error: {self.args[0] if self.args else ''}"
