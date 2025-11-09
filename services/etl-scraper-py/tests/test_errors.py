"""
Tests for errors.py - custom exception classes.
"""

import pytest
from errors import EtlError, ApiError, ScraperError, SchemaValidationError


class TestErrors:
    """Test custom exception classes."""

    def test_etl_error_inheritance(self):
        """Test that EtlError is a proper Exception subclass."""
        error = EtlError("Test ETL error")
        assert isinstance(error, Exception)
        assert str(error) == "Test ETL error"

    def test_api_error_inheritance(self):
        """Test that ApiError inherits from EtlError."""
        error = ApiError("Test API error")
        assert isinstance(error, EtlError)
        assert isinstance(error, Exception)
        assert str(error) == "Test API error"

    def test_scraper_error_inheritance(self):
        """Test that ScraperError inherits from EtlError."""
        error = ScraperError("Test scraper error")
        assert isinstance(error, EtlError)
        assert isinstance(error, Exception)
        assert str(error) == "Test scraper error"

    def test_schema_validation_error_inheritance(self):
        """Test that SchemaValidationError inherits from EtlError."""
        error = SchemaValidationError("Test schema error")
        assert isinstance(error, EtlError)
        assert isinstance(error, Exception)
        assert str(error) == "Test schema error"

    def test_error_hierarchy(self):
        """Test the exception hierarchy is correct."""
        api_error = ApiError("API issue")
        scraper_error = ScraperError("Scraping issue")
        schema_error = SchemaValidationError("Schema issue")

        # All should be EtlError instances
        assert isinstance(api_error, EtlError)
        assert isinstance(scraper_error, EtlError)
        assert isinstance(schema_error, EtlError)

        # But not interchangeable
        assert not isinstance(api_error, ScraperError)
        assert not isinstance(scraper_error, ApiError)
        assert not isinstance(schema_error, ScraperError)

    def test_error_with_custom_message(self):
        """Test errors can be created with custom messages."""
        messages = [
            "Network timeout",
            "Invalid credentials",
            "Page not found",
            "Data validation failed"
        ]

        for msg in messages:
            error = EtlError(msg)
            assert str(error) == msg

    def test_error_cause_preservation(self):
        """Test that exception chaining works properly."""
        original_error = ValueError("Original cause")
        try:
            raise EtlError("ETL failed") from original_error
        except EtlError as etl_error:
            assert etl_error.__cause__ is original_error
            assert isinstance(etl_error, EtlError)
